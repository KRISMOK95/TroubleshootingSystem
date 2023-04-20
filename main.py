import time
import paho.mqtt.client as mqtt
import ast
import threading
global_data = None

#region MQTT

MQTT_BROKER = "test.mosquitto.org"
MQTT_TOPIC = "example/topic"

def on_message(client, userdata, message):
    global global_data
    print("Message received via MQTT:")
    raw_data = message.payload.decode('utf-8')
    print(f"Row data: {raw_data}")
    print(f"Row data type: {type(raw_data)}")

    try:
        data_list =ast.literal_eval(raw_data)
        global_data = data_list

    except (ValueError, SyntaxError):
        print("Received message is not a valid list.")

client = mqtt.Client()
client.connect(MQTT_BROKER, 1883)
client.on_message = on_message
client.subscribe(MQTT_TOPIC)
#client.loop_start()

def mqtt_client_loop():
    while True:
        client.loop(timeout=1.0)

#endregion

# region Real-time vs Standard data

class TroubleshootingSystem:
    def __init__(self, real_time_data, standard_data):
        self.real_time_data = real_time_data
        self.standard_data = standard_data

    def analyze_data(self):
        issues = []

        # Compare real-time data to standard values
        if self.real_time_data['circulating_fluid_discharge_temperature'] > float(self.standard_data['set_temperature_range_celsius'].split("-")[1]):
            issues.append("High discharge temperature")

        if self.real_time_data['circulating_fluid_discharge_pressure'] > self.standard_data['pump_max_head_50Hz_60Hz_m']:
            issues.append("High discharge pressure")

        if self.real_time_data['electric_resistivity_and_conductivity_circulating_fluid'] < self.standard_data['minimum_resistivity']:
            issues.append("Low resistivity")

        return issues

    def suggest_solutions(self, issues):
        solutions = []

        for issue in issues:
            if issue == "High discharge temperature":
                solutions.append("Check for blockages in the cooling system or adjust the set temperature.")
            elif issue == "High discharge pressure":
                solutions.append("Inspect and clean the pump, or adjust the set pressure.")
            elif issue == "Low resistivity":
                solutions.append("Check the fluid for contaminants, or replace the fluid if necessary.")

        return solutions

# Initialize the troubleshooting system with real-time and standard data
real_time_data = {
    'circulating_fluid_discharge_temperature': 45,
    'circulating_fluid_discharge_pressure': 60,
    'electric_resistivity_and_conductivity_circulating_fluid': 0.5
}

standard_data = {
    'set_temperature_range_celsius': "5-40",
    'pump_max_head_50Hz_60Hz_m': 50,
    'minimum_resistivity': 0.6
}

troubleshooting_system = TroubleshootingSystem(real_time_data, standard_data)

# Analyze data to identify potential issues
issues = troubleshooting_system.analyze_data()

# Suggest solutions based on the identified issues
solutions = troubleshooting_system.suggest_solutions(issues)

print("Issues detected:", issues)
print("Suggested solutions:", solutions)

#endregion

#region AF22

def ask_question(question):
    print(question)
    return input().lower()

def troubleshoot_AL22():
    if ask_question("AL22 is being generated? (y/n): ") == "y":
        print("AL22: Circulating fluid discharge temp. sensor failure.")
        return

    if ask_question("Is ambient temperature out of the specification range? (y/n): ") == "y":
        print("This system cannot be used.")
        return

    if ask_question("Is external load out of the specification range? (y/n): ") == "y":
        print("This system cannot be used.")
        return

    if ask_question("Is there enough ventilation space? (y/n): ") == "n":
        if ask_question("Is the dustproof filter too dusty? (y/n): ") == "y":
            print("Clean the dustproof filter.")
            return

    sensor_input = ask_question("Check the circulating fluid temperature sensor. (Normal/Error): ")
    if sensor_input == "error":
        sensor_input = ask_question("Check the circulating fluid temperature sensor after it is replaced? (Normal/Error): ")

    flow_input = ask_question("Is flow rate of the circulating fluid less than 10 L/min? (y/n): ")
    if flow_input == "y":
        pump_input = ask_question("Check the pump performance. (Normal/Error): ")
        if pump_input == "normal":
            print("Connect a by-pass piping.")
            return
        else:
            print("Replace the pump.")
            return

    if ask_question("Is the circulating fluid contaminated? (y/n): ") == "y":
        print("Clean the circulating fluid circuit.")
        return

    pressure_input = ask_question("Check the pressure sensor in the refrigerant circuit. (Normal/Error): ")
    if pressure_input == "error":
        print("Replace the main board.")
        return

    refrigerant_input = ask_question("Check if refrigerant leaks. (With Leakage Yes/No Leakage No): ")
    if refrigerant_input == "with leakage yes":
        print("Repair the refrigerant circuit. Only a specialized operator is allowed to handle the refrigerant circuit.")
        return
    elif refrigerant_input == "no leakage no":
        power_input = ask_question("After stopping the power supply, does the same alarm go off again when the chiller is restarted? (y/n): ")
        if power_input == "y":
            print("Please contact SMC.")
            return
        else:
            print("Electronic expansion valve, which is a part of the refrigerant circuit, needs to be replaced. Only a specialized operator is allowed to handle the refrigerant circuit.")
            return
#endregion

#region Alarm flag
def process_alarm_flags():
    global global_data

    AF22 = False

    if global_data is None:
        return
    ALARM_FLAG_1_BIT_MEANING = {
        0: "Low level in tank",
        1: "High circulating fluid discharge temp",
        2: "Circulating fluid discharge temp. rise",
        3: "Circulating fluid discharge temp.",
        4: "High circulating fluid return temp..",
        5: "High circulating fluid discharge pressure",
        6: "Abnormal pump operation",
        7: "Circulating fluid discharge pressure rise",
        8: "Circulating fluid discharge pressure drop",
        9: "High compressor intake temp",
        10: "Low compressor intake temp.",
        11: "Low super heat temperature",
        12: "High compressor discharge pressure",
        14: "Refrigerant circuit pressure (high pressure side) drop",
        15: "Refrigerant circuit pressure (low pressure side) rise",
    }

    ALARM_FLAG_2_BIT_MEANING = {
        0: "Refrigerant circuit pressure (low pressure side) drop",
        1: "Compressor overload",
        2: "Communication error",
        3: "Memory error",
        4: "DC line fuse cut",
        5: "Circulating fluid discharge temp. sensor failure",
        6: "Circulating fluid return temp. sensor failure",
        7: "Compressor intake temp. sensor failure",
        8: "Circulating fluid discharge pressure sensor failure",
        9: "Compressor discharge pressure sensor failure",
        10: "Compressor intake pressure sensor failure",
        11: "Maintenance of pump",
        12: "Maintenance of fan motor",
        13: "Maintenance of compressor",
        14: "Contact input 1 signal detection alarm",
        15: "Contact input 2 signal detection alarm",
    }

    ALARM_FLAG_3_BIT_MEANING = {
        0: "Water leakage",
        1: "Electric resistivity/conductivity level rise",
        2: "Electric resistivity/conductivity level drop",
        3: "Electric resistivity/conductivity sensor error",

    }
    alarm_flag_1 = global_data[5]

    for bit, meaning in ALARM_FLAG_1_BIT_MEANING.items():
        bit_value = (alarm_flag_1 >> bit) & 1
        print(f"AF 1: {meaning} /// {bit_value}")
        if bit_value == 1:
            print(f"Occurred AF1: {meaning}")
    time.sleep(2)

    alarm_flag_2 = global_data[6]

    for bit, meaning in ALARM_FLAG_2_BIT_MEANING.items():
        bit_value = (alarm_flag_2 >> bit) & 1
        print(f"AF2 : {meaning} /// {bit_value}")
        if bit_value == 1:
            print(f"Occurred Alarm flag 2: {meaning}")
            if meaning == "Communication error":
                AF22 = True
    time.sleep(2)

    alarm_flag_3 = global_data[7]

    for bit, meaning in ALARM_FLAG_3_BIT_MEANING.items():
        bit_value = (alarm_flag_3 >> bit) & 1
        print(f"AF3 : {meaning} /// {bit_value}")
        if bit_value == 1:
            print(f"Occurred AF3: {meaning}")
    time.sleep(2)

    if AF22:
        troubleshoot_AL22()

    global_data = None
#endregion

while True:
    process_alarm_flags()
    time.sleep(1)