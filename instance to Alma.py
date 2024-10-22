instance_uri = "https://api.stage.sinopia.io/resource/70467908-9173-48ac-b476-03dac2bfc72f"
# change the instance_uri to the URI of the instance that you want to serialize for Alma RDF/XML.
# add api key and region for posting the resource to Alma
# https://github.com/LD4P/ils-middleware/wiki/Alma-APIs-in-Airflow

alma_api_key = "l8xxfeb00ad247e44c189a3ba9b282a2e222"
uri_region = "https://api-na.hosted.exlibrisgroup.com"

import requests
from rdflib import Graph, Namespace, URIRef
from rdflib import Namespace, URIRef, RDF, Graph
from rdflib.namespace import RDF
from lxml import etree as ET
from name_space.alma_ns import alma_namespaces

instance_uri = URIRef(instance_uri)
work_uri = None
instance_graph = Graph()
work_graph = Graph()
instance_graph.parse(instance_uri, format='json-ld')

# Define the bf and bflc namespaces
bf = Namespace("http://id.loc.gov/ontologies/bibframe/")
for prefix, url in alma_namespaces:
    instance_graph.bind(prefix, url)
work_uri = instance_graph.value(subject=URIRef(instance_uri), predicate=bf.instanceOf)



work_uri = URIRef(work_uri)

# Explicitly state that work_uri is of type bf:Work
work_graph.add((work_uri, RDF.type, bf.Work))
# add the work to the instance graph
instance_graph.add((instance_uri, bf.instanceOf, URIRef(work_uri)))
# serialize the instance graph
instance_alma_xml = instance_graph.serialize(format="pretty-xml", encoding="utf-8")

print(instance_graph.serialize(format='pretty-xml'))

tree = ET.fromstring(instance_alma_xml)
# apply xslt to normalize instance
xslt = ET.parse("xsl/normalize-instance-sinopia2alma.xsl")
transform = ET.XSLT(xslt)
instance_alma_xml = transform(tree)
instance_alma_xml = ET.tostring(
        instance_alma_xml, pretty_print=True, encoding="utf-8"
        )
# save the xml to a file
with open("alma-instance.xml", "wb") as f:
    f.write(instance_alma_xml)
print(instance_alma_xml.decode("utf-8"))
# handle 400, an update to the record in Alma
def parse_400(result):
    xml_response = ET.fromstring(result)
    xslt = ET.parse("xsl/put_mms_id.xsl")
    transform = ET.XSLT(xslt)
    result_tree = transform(xml_response)
    put_mms_id_str = str(result_tree)
    print(f"put_mms_id_str: {put_mms_id_str}")
    return put_mms_id_str

# post the instance to Alma
def NewInstancetoAlma():
    with open("alma-instance.xml", "rb") as f:
        data = f.read()

        alma_uri = (
            uri_region
            + "/almaws/v1/bibs?"
            + "from_nz_mms_id=&from_cz_mms_id=&normalization=&validate=false"
            + "&override_warning=true&check_match=false&import_profile=&apikey="
            + alma_api_key
        )
        # post to alma
        alma_result = requests.post(
            alma_uri,
            headers={
                "Content-Type": "application/xml; charset=utf-8",
                "Accept": "application/xml",
                "x-api-key": alma_api_key,
            },
            data=data,
        )
        print(f"alma result: {alma_result.status_code}\n{alma_result.text}")
        result = alma_result.content
        status = alma_result.status_code
        if status == 200:
            xml_response = ET.fromstring(result)
            mms_id = xml_response.xpath("//mms_id/text()")
            print(f"Created record {mms_id}")
        elif status == 400:
            # run xslt on the result in case the response is 400 and we need to update the record
            put_mms_id_str = parse_400(result)
            alma_update_uri = (
                uri_region
                + "/almaws/v1/bibs/"
                + put_mms_id_str
                + "?normalization=&validate=false&override_warning=true"
                + "&override_lock=true&stale_version_check=false&cataloger_level=&check_match=false"
                + "&apikey="
                + alma_api_key
            )
            putInstanceToAlma(
                alma_update_uri,
                data,
            )
        else:
            raise Exception(f"Unexpected status code from Alma API: {status}")

# update the instance in Alma
def putInstanceToAlma(
    alma_update_uri,
    data,
):
    put_update = requests.put(
        alma_update_uri,
        headers={
            "Content-Type": "application/xml; charset=UTF-8",
            "Accept": "application/xml",
        },
        data=data,
    )
    print(f"put update: {put_update.status_code}\n{put_update.text}")
    put_update_status = put_update.status_code
    result = put_update.content
    xml_response = ET.fromstring(result)
    put_mms_id = xml_response.xpath("//mms_id/text()")
    match put_update_status:
        case 200:
            print(f"Updated record {put_mms_id}")
        case 500:
            raise Exception(f"Internal server error from Alma API: {put_update_status}")
        case _:
            raise Exception(
                f"Unexpected status code from Alma API: {put_update_status}"
            )

# Call the function
NewInstancetoAlma()
