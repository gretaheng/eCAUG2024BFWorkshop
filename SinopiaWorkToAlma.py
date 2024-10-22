import requests
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import RDF
from lxml import etree as ET
from name_space.alma_ns import alma_namespaces
from copy import deepcopy

# Define URIs and API key
work_uri = [work uri]
instance_uri = [instance uri]
alma_api_key = [YOUR API KEY]
uri_region = [YOUR REGION]

work_uri = URIRef(work_uri)
print(work_uri)
work_graph = Graph().parse(work_uri)
bf = Namespace("http://id.loc.gov/ontologies/bibframe/")
for prefix, url in alma_namespaces:
    work_graph.bind(prefix, url)
print(work_graph)
# Explicitly state that work_uri is of type bf:Work
work_graph.add((work_uri, RDF.type, bf.Work))
work_graph.parse(work_uri)

# add the instance to the work graph
work_graph.add((work_uri, bf.hasInstance, URIRef(instance_uri)))

# serialize the work graph
bfwork_alma_xml = work_graph.serialize(format="pretty-xml", encoding="utf-8")
tree = ET.fromstring(bfwork_alma_xml)
print(ET.tostring(tree, pretty_print=True).decode("utf-8"))
# save the work graph to a file
with open("work_graph.xml", "wb") as f:
    f.write(bfwork_alma_xml)

from lxml import etree as ET
from copy import deepcopy

# Parse the XML file
tree = ET.parse('work_graph.xml')
work_graph = tree.getroot()

# Define namespaces
namespaces = {'bf': 'http://id.loc.gov/ontologies/bibframe/',
              'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
              'rdfs': 'http://www.w3.org/2000/01/rdf-schema#'}

# Find all bf:Work elements
works = work_graph.xpath('//bf:Work', namespaces=namespaces)

for work in works:
    work_about = work.attrib['{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about']

    # Find the bf:relatedTo element with the same rdf:resource attribute value
    related_to = work_graph.xpath(f'//bf:relatedTo[@rdf:resource="{work_about}"]', namespaces=namespaces)

    if related_to:
        # Remove the rdf:resource attribute from the bf:relatedTo element
        related_to[0].attrib.pop('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource', None)

        # Clone the bf:Work element and append it under the bf:relatedTo element
        cloned_work = deepcopy(work)
        related_to[0].append(cloned_work)

        # Remove the original bf:Work element that was cloned
        work.getparent().remove(work)

# Print the modified XML
print(ET.tostring(work_graph, pretty_print=True).decode())
# save the modified XML to a file
with open('bfwork_alma.xml', 'wb') as f:
    f.write(ET.tostring(work_graph, pretty_print=True))
    f.close()

# open the file and parse the XML
tree = ET.parse("bfwork_alma.xml")
xslt = ET.parse("xsl/normalize-work-sinopia2alma.xsl")
transform = ET.XSLT(xslt)
alma_xml = transform(tree)
alma_xml = ET.tostring(
        alma_xml, pretty_print=True, encoding="utf-8"
        )
# save the xml to a file
with open("alma-work.xml", "wb") as f:
    f.write(alma_xml)
print(alma_xml.decode("utf-8"))

# handle 400, an update to the record in Alma
def parse_400(result):
    xml_response = ET.fromstring(result)
    xslt = ET.parse("xsl/put_mms_id.xsl")
    transform = ET.XSLT(xslt)
    result_tree = transform(xml_response)
    put_mms_id_str = str(result_tree)
    print(f"put_mms_id_str: {put_mms_id_str}")
    return put_mms_id_str

# post the work to Alma
def NewWorktoAlma():
    with open("alma-work.xml", "rb") as f:
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
            putWorkToAlma(
                alma_update_uri,
                data,
            )
        else:
            raise Exception(f"Unexpected status code from Alma API: {status}")

# update the instance in Alma
def putWorkToAlma(
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
NewWorktoAlma()
