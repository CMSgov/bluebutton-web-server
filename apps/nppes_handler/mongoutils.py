#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4

from django.conf import settings
import os, json, sys
import datetime
from bson.code import Code
from bson.objectid import ObjectId
from bson import json_util
from pymongo import MongoClient, DESCENDING
from collections import OrderedDict



def to_json(results_dict):
    return json.dumps(results_dict, indent = 4, default=json_util.default)


def update_mongo_pjson(document, database_name="nppes", collection_name="pjson"):
    """Update a Provider JSON resource.  The resource must exist in this implementation.
    """
    l=[]
    response_dict=OrderedDict()
    invalid = False
    existing_document = None
    try:

        mc          = MongoClient(host='127.0.0.1', port=27017, document_class=OrderedDict)
        db          = mc[database_name]
        collection  = db[collection_name]

        myobject=collection.find_one({'number':document['number']})
        response_dict['number'] = document['number']
        if not myobject:
            response_dict['code']=404
            response_dict['errors']=["The record cannot be updated because it is not found in the database.",]

        else:
            document['_id'] = myobject['_id']
            myobjectid=collection.save(document)
            response_dict['code']=200
    except:
        response_dict['code'] = 500
        response_dict['errors']=[ str(sys.exc_info()), ]

    return response_dict


