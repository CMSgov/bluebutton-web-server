import json
import sys
import datetime

from collections import OrderedDict

from pymongo import MongoClient
from bson import json_util
from bson.objectid import ObjectId


def to_json(results_dict):
    return json.dumps(results_dict, indent=4, default=json_util.default)


def update_mongo_fhir(document, database_name, collection_name, id):
    """
    Update a FHIR resource.  The resource must exist in this implementation.
    """
    response_dict = OrderedDict()
    invalid = False
    existing_document = None
    try:
        mc = MongoClient(host='127.0.0.1',
                         port=27017,
                         document_class=OrderedDict)
        db = mc[database_name]
        collection = db[collection_name]

        if 'id' not in document:
            invalid = True
        else:
            if str(document['id']) != str(id):
                invalid = True
            if len(str(id)) != 24:
                invalid = True
        if not invalid:
            document['id'] = ObjectId(str(id))
            existing_document = collection.find_one({'_id': document['id']})

        if invalid:
            response_dict['code'] = 400
            response_dict['details'] = 'id was missing, incorrect, or ' \
                                       'malformed. id length must be 24.'
            return response_dict

        if not existing_document:
            response_dict['code'] = 400
            response_dict['details'] = 'An existing ID must be provided.'
            return response_dict

        document['_id'] = document['id']
        # FIXME: variable not used
        # existing_document_id = existing_document['_id']

        history_collection_name = '%s_history' % str(collection_name)
        history_collection = db[str(history_collection_name)]

        history_object = existing_document
        history_object['old_id'] = str(existing_document['_id'])

        del history_object['_id']

        history_collection.save(history_object)

        # Check for meta and add if missing or increment if present
        document['meta'] = OrderedDict()
        if 'meta' in existing_document:
            if 'version' in existing_document['meta']:
                document['meta']['version'] = existing_document['meta']['version'] + 1
            else:
                document['meta']['version'] = 1
        else:
            document['meta']['version'] = 1

        document['meta']['lastUpdated'] = '%sZ' % (datetime.datetime.utcnow().isoformat())

        myobjectid = collection.save(document)
        # now fetch the record we just wrote so that we write it back to the DB.
        myobject = collection.find_one({'_id': myobjectid})
        response_dict['code'] = 200
        myobject['id'] = str(myobjectid)
        del myobject['_id']
        response_dict['result'] = myobject
    except:
        response_dict['code'] = 500
        response_dict['details'] = str(sys.exc_info())
    return response_dict
