"""
for indri query parameter file generation
"""

import os
import json
import sys
import re
import argparse
import codecs
from templates import *
from myUtility.corpus import Query,ExpandedQuery

class IndriQueryFactory(object):
    """Take in query related parameters for indri and
    generate indri query file
    """
    def __init__(self,count,rule=None,
            use_stopper=False,date_when=None,
            numeric_compare=None):

        self._count,self._rule,self._use_stopper = count,rule,use_stopper

        

        if date_when:
            if date_when not in ["dateafter","datebefore", "datebetween"]:
                raise ValueError("When value %s is not supported" %(date_when))

        if numeric_compare is not None:
            if numeric_compare not in ["less","greater","between","equals"]:
                raise ValueError("Compare value %s is not supported" %(numeric_compare))


        self._date_when,self._numeric_compare = date_when,numeric_compare


    def _gene_query(self,file_path,queries,index,run_id,
                date_value=None,numeric_value=None,
                numeric_field_name=None):

        query_body = ""
        if self._rule is None:
            rule = ""
        else:
            rule = "<rule>%s</rule>" %self._rule

        if self._use_stopper:
            stopper = "<stopper>\n"
            stopwords = get_stopwords()
            for stopword in stopwords:
                stopper += "<word>%s</word>\n" %stopword 
            stopper += "</stopper>"
        else:
            stopper = ""



        for qid in queries: 
            sinlge_query_data = queries[qid]
            
            if isinstance(sinlge_query_data,Query):
                original_text = re.sub("[^\w]"," ",sinlge_query_data.text)
                if isinstance(sinlge_query_data,ExpandedQuery):
                    original_weight = sinlge_query_data.para_lambda
                    expanding_weight =  1-sinlge_query_data.para_lambda
                    expanding_string = ""
                    for term in sinlge_query_data.expanding_model:
                        term_weight = sinlge_query_data.expanding_model[term]
                        expanding_string += "%f %s " %(term_weight,term)
                
                    q_string = "#combine(%f #combine(%s) %f #weight(%s) " \
                                        %(original_weight,original_text,
                                          expanding_weight,expanding_string)

                else:
                    q_string = "#combine( %s )" %(original_text)

            elif isinstance(sinlge_query_data,str):
                q_string = sinlge_query_data.lower()
                q_string = re.sub("[^\w]"," ",q_string)
                q_string = "#combine(%s)" %(q_string)

            elif isinstance(sinlge_query_data,list):
                q_string = " ".join(sinlge_query_data)
                q_string = "#combine(%s)" %(q_string)
            
            elif isinstance(sinlge_query_data,dict):
                q_string = ""
                for term in sinlge_query_data:
                    weight = sinlge_query_data[term]
                    q_string += "%f %s " %(weight,term)

                q_string = "#weight(%s)" %(q_string)
            else:
                raise TypeError("unsupported value type %s for query data" %type(sinlge_query_data))

            
            if self._date_when:
                q_string = "#filrej(#%s(%s) %s)" %(self._date_when,date_value,
                                                        q_string)
            
            if self._numeric_compare is not None:
                q_string = "#filrej(#%s(%s %d) %s)" %(self._numeric_compare,
                                            numeric_field_name,numeric_value,q_string)

            query_body+=query_template.substitute(
                qid=qid,q_string=q_string)

        with codecs.open(file_path, 'w','utf-8') as f:
            f.write(structure_template.substitute(query_body=query_body,index=index,
                                                  run_id=run_id,count=str(self._count),
                                                  rule=rule,stopper=stopper))


    def gene_query_with_date_filter(self,file_path,queries,index,
                date_value,run_id="test"):

        self._gene_query(file_path,queries,index,run_id,date_value=date_value)


    def gene_query_with_numeric_filter(self,file_path,queries,index,
            numeric_value,numeric_field_name,run_id="test"):

        self._gene_query(file_path,queries,index,run_id,numeric_value=numeric_value,
                numeric_field_name=numeric_field_name)
