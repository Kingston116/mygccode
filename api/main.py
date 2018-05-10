# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import webapp2
from google.cloud import bigquery
import json
import datetime
import base64
import googleapiclient.discovery

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Hello, World!')

class TestPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        client = bigquery.Client()
        query_job = client.query("SELECT * FROM pubsubdata.pubdata order by time desc LIMIT 1")
        results = query_job.result()  # Waits for job to complete.
        dict = {}
        for row in results:
            dateStamp = datetime.datetime.now() 
            if isinstance(row['time'], datetime.datetime):
               dateStamp = row['time'].isoformat()
            dict = {"status":row['status'],"temperature":row['temperature'],"temperatureF":row['temperatureF'],"humidity":row['humidity'],"time":dateStamp,"COLevel":row['COLevel'],"GasADValue":row['GasADValue'],"LightLevel":row['LightLevel']}
        self.response.write(json.dumps(dict))
class TestMLPage(webapp2.RequestHandler):
    def get(self):
        project = "tidy-surge-200215"
        model = "hackathon"
        version = "flowers"
        img = base64.b64encode(open("daisy.jpg", "rb").read());
        jsonImg = {"instances":[{"image_bytes": {"b64": img},"key": "0"}]}
        user_input = jsonImg
        service = googleapiclient.discovery.build('ml', 'v1')
        name = 'projects/{}/models/{}'.format(project, model)
        if version is not None:
            name += '/versions/{}'.format(version)
        test = user_input
        response = service.projects().predict(
            name=name,
            body=test
        ).execute()
        if 'error' in response:
           raise RuntimeError(response['error'])
        print(response['predictions'])
        # [END predict_json]
        self.response.write(json.dumps(response['predictions']))


app = webapp2.WSGIApplication([('/', MainPage),('/getstatus', TestPage),('/getimage', TestMLPage),], debug=True)
def main():
    from paste import httpserver
    httpserver.serve(app, host='127.0.0.1')
    app.run()

if __name__ == '__main__':
    main()
