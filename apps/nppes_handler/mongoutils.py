import json
import sys

from collections import OrderedDict

from bson import json_util
from pymongo import MongoClient


def to_json(results_dict):
    return json.dumps(results_dict, indent=4, default=json_util.default)


def update_mongo_pjson(document, database_name='nppes', collection_name='pjson'):
    """
    Update a Provider JSON resource.
    The resource must exist in this implementation.
    """
    # l = []
    # invalid = False
    # existing_document = None
    response_dict = OrderedDict()
    try:
        mc = MongoClient(host='127.0.0.1', port=27017, document_class=OrderedDict)
        db = mc[database_name]
        collection = db[collection_name]

        myobject = collection.find_one({'number': document['number']})
        response_dict['number'] = document['number']
        if not myobject:
            response_dict['code'] = 404
            response_dict['errors'] = ['The record cannot be updated because it is not found in the database.']
        else:
            document['_id'] = myobject['_id']
            collection.save(document)
            response_dict['code'] = 200
    except Exception:
        response_dict['code'] = 500
        response_dict['errors'] = [str(sys.exc_info()), ]

    return response_dict
