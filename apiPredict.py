import argparse
import base64
import json

# [START import_libraries]
import googleapiclient.discovery
# [END import_libraries]
import six
# [START predict_json]
def predict_json(project, model, instances, version=None):
    """Send json data to a deployed model for prediction.
    Args:
        project (str): project where the Cloud ML Engine Model is deployed.
        model (str): model name.
        instances ([Mapping[str: Any]]): Keys should be the names of Tensors
            your deployed model expects as inputs. Values should be datatypes
            convertible to Tensors, or (potentially nested) lists of datatypes
            convertible to tensors.
        version: str, version of the model to target.
    Returns:
        Mapping[str: any]: dictionary of prediction results defined by the
            model.
    """
    # Create the ML Engine service object.
    # To authenticate set the environment variable
    # GOOGLE_APPLICATION_CREDENTIALS=<path_to_service_account_file>
    service = googleapiclient.discovery.build('ml', 'v1')
    name = 'projects/{}/models/{}'.format(project, model)

    if version is not None:
        name += '/versions/{}'.format(version)
    test = instances
    response = service.projects().predict(
        name=name,
        body=test
    ).execute()
    if 'error' in response:
        raise RuntimeError(response['error'])
    print(response['predictions'])
    return response['predictions']
# [END predict_json]

def main():
    """Send user input to the prediction service."""
    try:
       project = "tidy-surge-200215"
       model = "hackathon"
       version = "flowers"
       img = base64.b64encode(open("daisy.jpg", "rb").read());
       jsonImg = {"instances":[{"image_bytes": {"b64": img},"key": "0"}]}
       user_input = jsonImg
       predict_json(project, model, user_input, version)
    except KeyboardInterrupt:
       return
if __name__ == '__main__':
    main()
