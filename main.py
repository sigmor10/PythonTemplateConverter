import xml.etree.ElementTree as Et
from pathlib import Path
import yaml
import re


# helper class for marking strings as literal scalars
class LiteralStr(str):
    pass


# helper class to mark arrays/lists as flow style type
class FlowList(list):
    pass


# presenter method to force PyYaml to save data as literal scalars
def literal_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')


# presenter method to force PyYaml to save data as flow style data
def flow_list_presenter(dumper, data):
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)


# registering presenter methods with their respective helper classes
yaml.add_representer(LiteralStr, literal_presenter)
yaml.add_representer(FlowList, flow_list_presenter)


# Creates a dictionary containing information about a field stored in a template file
def create_field_dict(node):
    tmp = {
        "Name": str(node.attrib["name"]),
        "Type": str(node.attrib['type']),
        "Subtype": str(node.attrib['subtype']),
        "Caption": str(node.attrib['caption']),
    }

    # Adding default values to certain fields
    if tmp.get("Name") == "hrsFrom" or tmp.get("Name") == "from":
        tmp["DefaultVal"] = 6
    if tmp.get("Name") == "hrsTo" or tmp.get("Name") == "to":
        tmp["DefaultVal"] = 16

    # Changing subtype to match new format
    if tmp.get("Name") == "hrsFrom" or tmp.get("Name") == "hrsTo":
        tmp["Subtype"] = "time"
    elif tmp.get("Name") == "from" or tmp.get("Name") == "to":
        tmp["Subtype"] = "datetime"

    # Extracting Lookup query if one exists for this field
    if node.text is not None and len(node.text) > 0:
        tmp["LookupQuery"] = str(node.text).strip()
        if tmp.get('Subtype') == "multiList":
            tmp["Subtype"] = "multilist"

    return tmp


# Creates a small dictionary containing information about single header cell stored in a template
def create_header_dict(node):
    colspan = int(node.attrib['colspan']) if 'colspan' in node.attrib else None

    text = node.text
    tmp = {
        "Text": ' ' if text is None or text == '' else text.strip().replace("\x9C", "ś"),
    }

    if colspan is not None:
        tmp["Colspan"] = colspan

    return tmp


# Creates a dictionary containing minimal information  needed for document template
def create_config_dict(node):
    pdf = node.find('pdf')
    margins = [
        int(pdf.attrib['m_bot']),
        int(pdf.attrib['m_top']),
        int(pdf.attrib['m_right']),
        int(pdf.attrib['m_left'])
    ]

    widths = node.find('pdf_object').attrib['cell_widths']
    cell_widths = [float(x.strip()) for x in widths.split(',')]

    tmp = {
        "Margins": FlowList(margins),
        "CellWidths": FlowList(cell_widths)
    }

    return tmp


# Creates a dictionary with all data needed for a template of a form
def create_form_dict(node):
    fields = []
    for field in node.find('fields').findall('field'):
        fields.append(create_field_dict(field))

    tmp = {
        "Title": node.find('title').text,
        "TitleOnPage": node.find('titleOnWeb').text,
        "Info": node.find('infoOnWeb').text,
        "Fields": fields
    }
    return tmp


def newline_reducer(match):
    m_string = match.group(0)
    count = m_string.count('\n')

    if count > 2:
        return "\n\n"
    else:
        return "\n" * count


# Creates dictionary containing all data needed for a report template
def create_report_dict(node, filename):
    disp = node.find('display_result')

    # Gathering all report header fields from a src template
    headers = []
    for row in disp.find('header').findall('tr'):
        tmp = []
        for cell in row.findall('td'):
            tmp.append(create_header_dict(cell))

        headers.append(tmp)

    # Gathering and cleaning sql query from drc template
    query_tmp = node.find('sql').find("sql_question").text.strip()
    query_tmp = query_tmp.replace('\xa0', " ")
    query_tmp = query_tmp.replace('\r', "")
    query_tmp = query_tmp.replace('\t', "")
    query_tmp = query_tmp.replace('\x9C', "ś")

    # Regexes responsible for adapting query for .Net Dapper and cleaning unnecessary whitespaces
    query_tmp = re.sub(r'@(\w+)', r'@\1_sql', query_tmp)
    query_tmp = re.sub(r'(\(\s*)?\?(\w+)\?(\s*\))?', r'@\2', query_tmp)
    query_tmp = re.sub(r'(\s*)(\n+)(\s*)', newline_reducer, query_tmp)

    sql_text_final = query_tmp.strip()
    if '\n' in sql_text_final and not sql_text_final.endswith('\n'):
        sql_text_final += '\n'

    # Wrapping query with LiteralStr so in output file its saved as literal scalar
    query = LiteralStr(sql_text_final)

    tmp = {
        "Title": disp.find("title").text,
        "Headers": headers,
        "Query": query,
        "FileName": filename,
        "PdfConfig": create_config_dict(disp)
    }
    return tmp


# Collects created dictionaries into one dict, then creates yaml
# file with collective dictionary as contents
def gen_yaml_template(path, form, report):
    data = {
        "Form": form,
        "Report": report
    }

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, width=500)


# Handles conversion by delegating tasks step by step
def convert_templates(xml_list, in_path, out_path):
    for xml_path in xml_list:
        with open(xml_path, "r", encoding="iso-8859-2") as f:
            data = f.read()
            # decoding xml file structure onto pre-made classes
            root = Et.fromstring(data)
            filename = root.find('fileName').attrib['file']
            form = create_form_dict(root.find("get_data"))
            report = create_report_dict(root.find('report'), filename)

            # saving template as new yml file
            rel_path = Path(xml_path).relative_to(in_path)
            target_path = Path(out_path) / rel_path.parent
            target_path.mkdir(parents=True, exist_ok=True)

            final_path = target_path / (Path(xml_path).stem + ".yml")
            gen_yaml_template(final_path, form, report)


# Gets a list of all xml files within a directory, includes recursive paths
def get_all_xml(folder):
    return list(Path(folder).rglob('*.xml'))


if __name__ == '__main__':
    source_path = "./input"
    output_path = "./out"
    templates = get_all_xml(source_path)
    Path("out").mkdir(parents=True, exist_ok=True)
    convert_templates(templates, source_path, output_path)
