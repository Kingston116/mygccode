import remi.gui as gui
import argparse
import base64
import json
import sys
import time
import os
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import pubsub
from remi import start, App
from threading import Thread as start_new_thread
from google.cloud import bigquery
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'service_account.json'

API_SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

API_VERSION = 'v1'

DISCOVERY_API = 'https://cloudiot.googleapis.com/$discovery/rest'

SERVICE_NAME = 'cloudiot'
global apiPayload 
def discovery_url(api_key):

  """Construct the discovery url for the given api key."""

  return '{}?version={}&key={}'.format(DISCOVERY_API, API_VERSION, api_key)

class RemoteLabel(gui.Label):
    apiPayload = ''
    def __init__(self, text, **kwargs):
        super(RemoteLabel, self).__init__(text, **kwargs)

    # api function
    def api_set_text(self, value1, value2):
        self.set_text('parameters: %s - %s' % (value1, value2))
        headers = {'Content-type': 'text/plain'}
        return ['OK', headers]
        
    # api function
    def getstatus(self):
        headers = {'Content-type': 'text/plain'}
        print("==========" + self.apiPayload)
        return [self.apiPayload, headers]


class MyApp(App):
    def __init__(self, *args):
        super(MyApp, self).__init__(*args)

    def main(self):
        wid = gui.VBox()

        #the 'id' param allows to have an alias in the url to refer to the widget that will manage the call
        self.lbl = RemoteLabel('type in other page url "http://127.0.0.1:8082/label/api_set_text?value1=text1&value2=text2" !', width='80%', height='50%', id='label')
        self.lbl.style['margin'] = 'auto'

        # appending a widget to another, the first argument is a string key
        wid.append(self.lbl)

        # returning the root widget
        return wid
        
class Server(object):

  """Represents the state of the server."""



  def __init__(self, service_account_json, api_key):

    credentials = ServiceAccountCredentials.from_json_keyfile_name(

        service_account_json, API_SCOPES)

    if not credentials:

      sys.exit('Could not load service account credential from {}'.format(

          service_account_json))



    self._service = discovery.build(

        SERVICE_NAME,

        API_VERSION,

        discoveryServiceUrl=discovery_url(api_key),

        credentials=credentials)

  def _update_device_config(self, project_id, region, registry_id, device_id,
                            data, fan_on_thresh,  fan_off_thresh):
    """Push the data to the given device as configuration.
    config_data = None
    if data['temperature'] < fan_off_thresh:
      # Turn off the fan.
      config_data = {'fan_on': False}
      print 'Temp:', data['temperature'],'C. Setting fan state for device', device_id, 'to off.'
    elif data['temperature'] > fan_on_thresh:
      # Turn on the fan
      config_data = {'fan_on': True}
      print 'Temp:', data['temperature'],'C. Setting fan state for device', device_id, 'to on.'
    else:
      # Temperature is OK, don't need to push a new config.
      return

    config_data_json = json.dumps(config_data)
    body = {
        # The device configuration specifies a version to update, which can be
        # used to avoid having configuration updates race. In this case, we
        # use the special value of 0, which tells Cloud IoT to always update the
        # config.
        'version_to_update': 0,
        'data': {

            # The data is passed as raw bytes, so we encode it as base64. Note

            # that the device will receive the decoded string, and so you do not

            # need to base64 decode the string on the device.

            'binary_data': base64.b64encode(config_data_json)

        }

    }



    device_name = 'projects/{}/locations/{}/registries/{}/devices/{}'.format(

        project_id, region, registry_id, device_id)



    request = self._service.projects().locations().registries().devices(

    ).modifyCloudToDeviceConfig(

        name=device_name, body=body)

    return request.execute()

    """

    print(data)

    return

  def callback(self,message):

        print(">>>>>>>>> " + message.data)
        RemoteLabel.apiPayload = message.data
        ROWS =  [(message.data)]
        dataset = bigquery.Dataset(client.dataset('pubsubdata'))
        table_ref = dataset.table('test')
        table = client.get_table(table_ref)
        client = bigquery.Client()
        client.insert_rows(table, ROWS)
        print("<<<<<<<<<" + RemoteLabel.apiPayload) 

        message.ack()

  def run(self, project_id, pubsub_topic, pubsub_subscription):

    """The main loop for the device. Consume messages from the Pub/Sub topic."""

    pubsub_client = pubsub.SubscriberClient()

    topic_name = 'projects/{}/topics/{}'.format(project_id, pubsub_topic)

    subscription_name ='projects/{}/subscriptions/{}'.format(project_id, pubsub_subscription)

    subscription = pubsub_client.subscribe(subscription_name)


    print('Server running. Consuming telemetry events from', topic_name)



    while True:

      # Pull from the subscription, waiting until there are messages.

      future = subscription.open(self.callback)

      results = future.result()

      #print(results)

      #results = subscription.pull(return_immediately=False)

      for ack_id, message in results:

        # print '.'

        data = json.loads(message.data)

        # Get the registry id and device id from the attributes. These are

        # automatically supplied by IoT, and allow the server to determine which

        # device sent the event.

        device_project_id = message.attributes['projectId']

        device_registry_id = message.attributes['deviceRegistryId']

        device_id = message.attributes['deviceId']

        device_region = message.attributes['deviceRegistryLocation']



        # Send the config to the device.

        self._update_device_config(device_project_id, device_region,

                                   device_registry_id, device_id, data)

        # state change updates throttled to 1 sec by pubsub. Obey or crash. 

        time.sleep(1)



      if results:


       # Acknowledge the consumed messages. This will ensure that they are not

        # redelivered to this subscription.

        subscription.acknowledge([ack_id for ack_id, message in results])





def parse_command_line_args():

  """Parse command line arguments."""

  parser = argparse.ArgumentParser(

      description='Example of Google Cloud IoT registry and device management.')

  # Required arguments

  parser.add_argument(

      '--project_id', required=True, help='GCP cloud project name.')

  parser.add_argument(

      '--pubsub_topic',

      required=True,

      help=('Google Cloud Pub/Sub topic name.'))

  parser.add_argument(

      '--pubsub_subscription',

      required=True,

      help='Google Cloud Pub/Sub subscription name.')

  parser.add_argument('--api_key', required=True, help='Your API key.')



  # Optional arguments

  parser.add_argument(

      '--service_account_json',

      default='service_account.json',


     help='Path to service account json file.')



  return parser.parse_args()


if __name__ == "__main__":
    # starts the webserver
    # optional parameters
    # start(MyApp,address='127.0.0.1', port=8081, multiple_instance=False,enable_file_cache=True, update_interval=0.1, start_browser=True)
    args = parse_command_line_args()
    server = Server(args.service_account_json, args.api_key)
    oThread = start_new_thread(target=server.run, args=(args.project_id, args.pubsub_topic, args.pubsub_subscription,))
    oThread.setDaemon(True)
    oThread.start()
    start(MyApp, debug=True, address='127.0.0.1', port=8082)
