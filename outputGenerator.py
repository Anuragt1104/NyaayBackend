import re
import json
from typing import List

class OutputGenerator:
    def __init__(self):
        self.filter_exclusion = re.compile(r'.*@example\.com|John Smith|John Doe|Jane Smith|Jane Doe')
        self.yyyy_mm_dd_format = r'\d{4}-\d{2}-\d{2}'
        self.dd_mm_yyyy_format = r'\d{2}.\d{2}.\d{4}'
        self.field_list = [
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

    def is_valid_value(self, input_string):
        if not input_string:
            return False
        if re.match(self.filter_exclusion, input_string):
            print("Excluding value:", input_string)
            return False
        return True

    def get_date_value(self, input_string):
        try:
            if re.match(self.yyyy_mm_dd_format, input_string):
                return input_string
            elif re.match(self.dd_mm_yyyy_format, input_string):
                date_obj = datetime.datetime.strptime(input_string, '%d.%m.%Y')
                return date_obj.strftime('%Y-%m-%d')
        except Exception as e:
            print("Error parsing date:", e)
        return input_string

    def extract_field(self, obj, item, field_name):
        if field_name in item:
            val = item[field_name]
            if isinstance(val, str):
                if self.is_valid_value(val):
                    if field_name.lower().endswith("date"):
                        val = self.get_date_value(val)
                    obj[field_name] = val
            elif isinstance(val, list):
                if field_name in obj and isinstance(obj[field_name], list):
                    obj[field_name] += val
                else:
                    obj[field_name] = val

    def generate(self, input_list, _id):
        obj = {}
        for input_item in input_list:
            try:
                item = json.loads(input_item)
                for field in ["Court Name", "Petition Type", "Order Date", "Case Number", "Case Date"] + self.field_list:
                    self.extract_field(obj, item, field)
            except Exception as e:
                print("Error processing:", input_item)
                print("Error:", e)
        obj["id"] = _id
        return json.dumps(obj)

    def generate_efiling_output(self, input_list, _id):
        obj = {}
        for input_item in input_list:
            try:
                item = json.loads(input_item)
                for key in item.keys():
                    self.extract_field(obj, item, key)
                    print("Key:", key, ", Value:", obj.get(key))
            except Exception as e:
                print("Error processing:", input_item)
                print("Error:", e)
        obj["id"] = _id
        return json.dumps(obj)

if __name__ == "__main__":
    output_generator = OutputGenerator()
    input_strings = [
        "jane@example.com",
        "John Doe",
        "Jane Doe",
        "John Smith",
        "Dheerendra Pandey John",
        "dheerendra@gmail.com"
    ]

    for input_string in input_strings:
        print("Input:", input_string, "Valid:", output_generator.is_valid_value(input_string))

    print(re.match(output_generator.yyyy_mm_dd_format, "2023-03-02"))
    print(re.match(output_generator.dd_mm_yyyy_format, "02.03.2023"))
