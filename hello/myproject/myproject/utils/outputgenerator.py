import re
import json
import datetime

filter_exclusion = r'.*@example\.com|John Smith|John Doe|Jane Smith|Jane Doe'
yyyy_mm_dd_format = r'\d{4}-\d{2}-\d{2}'
dd_mm_yyyy_format = r'\d{2}.\d{2}.\d{4}'
field_list = [
    "Petitioners",
    "Respondents",
    "Prayer",
    "Submissions",
    "Counsels",
    "Judges",
    "Key Observations",
    "Citations",
    "Final Judgement",
    "Concise Summary",
    "Key Timelines"
]

def generate_with_translation(self, input_list, completions_controller):
    prompt = "Perform exact Hindi Translation of the following text excluding any abbreviations or dates:"
    output_without_translation = self.generate(input_list, None)
    obj = json.loads(output_without_translation)
    translated_output = {}

    for field in field_list:
        if field in obj and isinstance(obj[field], list):
            input_array = obj[field]
            new_item = []
            for i in range(len(input_array)):
                new_item.append(completions_controller.complete_translation_prompt(prompt + ":" + input_array[i]))
            translated_output[field] = new_item

    translations = []
    hindi = {"Hindi": translated_output}
    translations.append(hindi)
    obj["Translations"] = translations
    return json.dumps(obj)

def add_translation(self, completions_controller, prompt, obj, translated_output, field_name):
    if field_name in obj and obj[field_name]:
        translated_output[field_name] = completions_controller.complete_translation_prompt(prompt + ":" + obj[field_name])

def generate(input_list, _id):
    obj = {}
    for input_string in input_list:
        print("Input String: ",input_string)
        try:
            item = json.loads(input_string)
            extract_field(obj, item, "Court Name")
            extract_field(obj, item, "Petition Type")
            extract_field(obj, item, "Order Date")
            extract_field(obj, item, "Case Number")
            extract_field(obj, item, "Case Date")
            for field in field_list:
                if field in item and isinstance(item[field], list):
                    if field in obj and isinstance(obj[field], list):
                        obj[field] += item[field]
                    else:
                        obj[field] = item[field]
        except Exception as e:
            print(f"Error processing: {input_string}")
            print(str(e))

    obj["id"] = _id
    return json.dumps(obj)

def extract_field(obj, item, field_name):
    if field_name in item and item[field_name]:
        val_object = item[field_name]
        if isinstance(val_object, str) and _is_valid_value(val_object):
            if field_name.lower().endswith("date"):
                formatted_date = _get_date_value(val_object)
                if formatted_date:
                    obj[field_name] = formatted_date
            else:
                obj[field_name] = val_object
        elif isinstance(val_object, list):
            if field_name in obj and isinstance(obj[field_name], list):
                obj[field_name] += val_object
            else:
                obj[field_name] = val_object

def _get_date_value(self, input_string):
    try:
        datetime_obj = datetime.datetime.strptime(input_string, "%d.%m.%Y")
        return datetime_obj.strftime("%Y-%m-%d")
    except ValueError:
        try:
            datetime_obj = datetime.datetime.strptime(input_string, "%Y-%m-%d")
            return datetime_obj.strftime("%Y-%m-%d")
        except ValueError:
            print(f"Invalid date format: {input_string}")
            return None

def _is_valid_value( input_string):
    if not filter_exclusion:
        return True
    regex = re.compile(filter_exclusion)
    return not regex.match(input_string)

def generate_efiling_output(input_list, id):
    obj = {}
    for input_string in input_list:
        try:
            item = json.loads(input_string)
            keys = item.keys()
            for key in keys:
                extract_field(obj, item, key)
                print("Key: " + key + ", Value: " + obj.get(key, ""))
        except Exception as e:
            print("Error processing:", input_string)
            print(e)

    obj["id"] = id
    return json.dumps(obj)
