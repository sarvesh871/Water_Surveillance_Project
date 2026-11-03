#include <WiFi.h>
#include <WebServer.h>

// =====================================================
// WIFI SETTINGS
// =====================================================

const char* WIFI_SSID = "ESP_WiFi";
const char* WIFI_PASSWORD = "12341234";

// Static IP for ESP32 Access Point
IPAddress local_IP(192, 168, 100, 1);
IPAddress gateway(192, 168, 100, 1);
IPAddress subnet(255, 255, 255, 0);

// =====================================================
// WEB SERVER
// =====================================================

WebServer server(80);

// =====================================================
// 4-IN-1 SENSOR UART
// =====================================================

// UART2
// RX = GPIO16
// TX = GPIO17

HardwareSerial sensorSerial(2);

// =====================================================
// ANALOG SENSORS
// =====================================================

const int TURBIDITY_PIN = 34;
const int TDS_PIN = 35;

// TDS sampling configuration
const int TDS_SAMPLES = 30;
const unsigned long TDS_INTERVAL = 1000;

// =====================================================
// SENSOR VARIABLES
// =====================================================

float phValue = 0.0;

int waterLevel = 0;
int lightValue = 0;

float temperatureF = 0.0;
float temperatureC = 0.0;

float turbidityRaw = 0.0;

float tdsRawADC = 0.0;
float tdsVoltage = 0.0;
float tdsValue = 0.0;

// =====================================================
// UART BUFFER
// =====================================================

String uartBuffer = "";

// =====================================================
// TIMERS
// =====================================================

unsigned long lastTurbidityRead = 0;
unsigned long lastTDSRead = 0;

const unsigned long TURBIDITY_INTERVAL = 1000;

// =====================================================
// SENSOR STATUS
// =====================================================

bool sensorReceived = false;

unsigned long lastSensorUpdate = 0;

// =====================================================
// WEB PAGE
// =====================================================

const char MAIN_PAGE[] PROGMEM = R"rawliteral(

<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Water Quality Monitoring</title>

<style>

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family: Arial, sans-serif;

    background: #eef7fb;

    color: #222;
}

.header {

    background: #0077b6;

    color: white;

    padding: 20px;

    text-align: center;
}

.header h1 {

    margin: 0;

    font-size: 26px;
}

.header p {

    margin: 8px 0 0;

    font-size: 14px;
}

.container {

    max-width: 900px;

    margin: 25px auto;

    padding: 15px;
}

.status {

    background: white;

    padding: 15px;

    border-radius: 12px;

    margin-bottom: 20px;

    box-shadow: 0 2px 8px rgba(0,0,0,0.1);

    text-align: center;
}

.status-dot {

    display: inline-block;

    width: 10px;

    height: 10px;

    background: #22c55e;

    border-radius: 50%;

    margin-right: 6px;
}

.grid {

    display: grid;

    grid-template-columns:
        repeat(auto-fit, minmax(180px, 1fr));

    gap: 15px;
}

.card {

    background: white;

    padding: 20px;

    border-radius: 15px;

    text-align: center;

    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.card h2 {

    font-size: 16px;

    margin: 0 0 12px;

    color: #555;
}

.value {

    font-size: 30px;

    font-weight: bold;

    color: #0077b6;
}

.unit {

    font-size: 13px;

    color: #777;

    margin-top: 5px;
}

.footer {

    text-align: center;

    color: #777;

    margin-top: 25px;

    font-size: 13px;
}

</style>

</head>

<body>

<div class="header">

    <h1>Water Quality Monitoring</h1>

    <p>ESP32 IoT Prototype</p>

</div>

<div class="container">

    <div class="status">

        <span class="status-dot"></span>

        <span id="status">
            Connected
        </span>

        <br>

        <small>
            Last update:
            <span id="updateTime">--</span>
        </small>

    </div>

    <div class="grid">

        <div class="card">

            <h2>pH</h2>

            <div class="value"
                 id="ph">
                --
            </div>

            <div class="unit">
                pH
            </div>

        </div>

        <div class="card">

            <h2>Water Level</h2>

            <div class="value"
                 id="water">
                --
            </div>

            <div class="unit">
                Sensor Value
            </div>

        </div>

        <div class="card">

            <h2>Light</h2>

            <div class="value"
                 id="light">
                --
            </div>

            <div class="unit">
                Sensor Value
            </div>

        </div>

        <div class="card">

            <h2>Temperature</h2>

            <div class="value"
                 id="temperature">
                --
            </div>

            <div class="unit">
                °C
            </div>

        </div>

        <div class="card">

            <h2>Turbidity</h2>

            <div class="value"
                 id="turbidity">
                --
            </div>

            <div class="unit">
                Raw ADC
            </div>

        </div>

        <div class="card">

            <h2>TDS</h2>

            <div class="value" id="tds">
                --
            </div>

            <div class="unit">
                Estimated ppm
            </div>

        </div>

    </div>

    <div class="footer">

        Data automatically refreshes every 5 seconds

    </div>

</div>

<script>

function updateData() {

    fetch('/data')

    .then(response => {

        if (!response.ok) {

            throw new Error("Network response error");

        }

        return response.json();

    })

    .then(data => {

        document.getElementById("ph").innerText =
            data.ph.toFixed(2);

        document.getElementById("water").innerText =
            data.water;

        document.getElementById("light").innerText =
            data.light;

        document.getElementById("temperature").innerText =
            data.temperature.toFixed(2);

        document.getElementById("turbidity").innerText =
            Number(data.turbidity).toFixed(2);

        document.getElementById("tds").innerText =
            Number(data.tds).toFixed(2);

        document.getElementById("updateTime").innerText =
            new Date().toLocaleTimeString();

        document.getElementById("status").innerText =
            "Connected";

    })

    .catch(error => {

        document.getElementById("status").innerText =
            "Connection Error";

    });

}

// Load immediately

updateData();

// Then every 5 seconds

setInterval(updateData, 5000);

</script>

</body>

</html>

)rawliteral";

// =====================================================
// SETUP
// =====================================================

void setup()
{
    Serial.begin(115200);

    delay(1000);

    Serial.println();
    Serial.println("================================");
    Serial.println(" WATER QUALITY IoT SYSTEM");
    Serial.println("================================");

    // -----------------------------------------------
    // 4-IN-1 SENSOR UART
    // -----------------------------------------------

    sensorSerial.begin(
        9600,
        SERIAL_8N1,
        16,
        17
    );

    Serial.println("4-in-1 sensor UART started");
    Serial.println("RX = GPIO16");
    Serial.println("TX = GPIO17");

    // -----------------------------------------------
    // TURBIDITY SENSOR
    // -----------------------------------------------

    pinMode(TURBIDITY_PIN, INPUT);
    pinMode(TDS_PIN, INPUT);

    analogReadResolution(12);

    // TDS module specification states 0-2.3 V analog output.
    // 11 dB attenuation provides a suitable ESP32 ADC range.
    analogSetPinAttenuation(TDS_PIN, ADC_11db);

    Serial.println("Turbidity sensor = GPIO34");
    Serial.println("TDS sensor = GPIO35");

    // -----------------------------------------------
    // WIFI ACCESS POINT
    // -----------------------------------------------

    WiFi.mode(WIFI_AP);

    WiFi.softAPConfig(
        local_IP,
        gateway,
        subnet
    );

    WiFi.softAP(
        WIFI_SSID,
        WIFI_PASSWORD
    );

    delay(500);

    Serial.println();
    Serial.println("WiFi Access Point started");

    Serial.print("WiFi Name: ");
    Serial.println(WIFI_SSID);

    Serial.print("IP Address: ");
    Serial.println(WiFi.softAPIP());

    // -----------------------------------------------
    // WEB ROUTES
    // -----------------------------------------------

    server.on(
        "/",
        HTTP_GET,
        handleRoot
    );

    server.on(
        "/data",
        HTTP_GET,
        handleData
    );

    server.on(
        "/status",
        HTTP_GET,
        handleStatus
    );

    server.begin();

    Serial.println();
    Serial.println("Web server started");

    Serial.println("--------------------------------");
    Serial.print("Open browser: http://");
    Serial.println(WiFi.softAPIP());
    Serial.println("--------------------------------");
}

// =====================================================
// MAIN LOOP
// =====================================================

void loop()
{
    // Handle web requests
    server.handleClient();

    // Read 4-in-1 UART data
    readSensorUART();

    // Read turbidity every 1 second
    if (
        millis() - lastTurbidityRead
        >= TURBIDITY_INTERVAL
    )
    {
        readTurbidity();

        lastTurbidityRead = millis();
    }

    // Read TDS every 1 second
    if (millis() - lastTDSRead >= TDS_INTERVAL)
    {
        readTDS();
        lastTDSRead = millis();
    }
}

// =====================================================
// READ 4-IN-1 SENSOR
// =====================================================

void readSensorUART()
{
    while (sensorSerial.available())
    {
        char c = sensorSerial.read();

        // End of line
        if (c == '\n')
        {
            uartBuffer.trim();

            if (uartBuffer.length() > 0)
            {
                parseSensorData(uartBuffer);
            }

            uartBuffer = "";
        }

        else if (c != '\r')
        {
            uartBuffer += c;

            // Safety limit
            if (uartBuffer.length() > 150)
            {
                uartBuffer = "";
            }
        }
    }
}

// =====================================================
// PARSE SENSOR DATA
// =====================================================
//
// Expected:
//
// PH:7.38, W:69, L:51, T:75,
//
// =====================================================

void parseSensorData(String data)
{
    data.trim();

    Serial.print("Sensor: ");
    Serial.println(data);

    int phStart = data.indexOf("PH:");

    int wStart = data.indexOf("W:");

    int lStart = data.indexOf("L:");

    int tStart = data.indexOf("T:");

    // Make sure all fields exist
    if (
        phStart < 0 ||
        wStart < 0 ||
        lStart < 0 ||
        tStart < 0
    )
    {
        Serial.println("Invalid sensor packet");

        return;
    }

    // -----------------------------------------------
    // pH
    // -----------------------------------------------

    int phEnd = data.indexOf(",", phStart);

    if (phEnd < 0)
    {
        return;
    }

    float newPH =
        data.substring(
            phStart + 3,
            phEnd
        ).toFloat();

    // -----------------------------------------------
    // Water Level
    // -----------------------------------------------

    int wEnd = data.indexOf(",", wStart);

    if (wEnd < 0)
    {
        return;
    }

    int newWater =
        data.substring(
            wStart + 2,
            wEnd
        ).toInt();

    // -----------------------------------------------
    // Light
    // -----------------------------------------------

    int lEnd = data.indexOf(",", lStart);

    if (lEnd < 0)
    {
        return;
    }

    int newLight =
        data.substring(
            lStart + 2,
            lEnd
        ).toInt();

    // -----------------------------------------------
    // Temperature
    // -----------------------------------------------

    int tEnd = data.indexOf(",", tStart);

    if (tEnd < 0)
    {
        tEnd = data.length();
    }

    float newTemperatureF =
        data.substring(
            tStart + 2,
            tEnd
        ).toFloat();

    // -----------------------------------------------
    // Temperature conversion
    // -----------------------------------------------

    float newTemperatureC =
        (newTemperatureF - 32.0)
        * 5.0
        / 9.0;

    // -----------------------------------------------
    // Save valid values
    // -----------------------------------------------

    phValue = newPH;

    waterLevel = newWater;

    lightValue = newLight;

    temperatureF = newTemperatureF;

    temperatureC = newTemperatureC;

    sensorReceived = true;

    lastSensorUpdate = millis();
}

// =====================================================
// READ TURBIDITY
// =====================================================

void readTurbidity()
{
    const int samples = 100;

    long totalADC = 0;
    long totalMilliVolts = 0;

    int minimum = 4095;
    int maximum = 0;

    for (int i = 0; i < samples; i++)
    {
        int adc = analogRead(TURBIDITY_PIN);
        int milliVolts = analogReadMilliVolts(TURBIDITY_PIN);

        totalADC += adc;
        totalMilliVolts += milliVolts;

        if (adc < minimum) minimum = adc;
        if (adc > maximum) maximum = adc;

        delayMicroseconds(500);
    }

    turbidityRaw = totalADC / (float)samples;

    float averageVoltage =
        totalMilliVolts / (1000.0 * samples);

    Serial.print("Turbidity ADC average: ");
    Serial.println(turbidityRaw, 2);

    Serial.print("ADC min/max: ");
    Serial.print(minimum);
    Serial.print(" / ");
    Serial.println(maximum);

    Serial.print("Average turbidity voltage: ");
    Serial.print(averageVoltage, 3);
    Serial.println(" V");
}

// =====================================================
// READ TDS SENSOR
// =====================================================

void readTDS()
{
    unsigned long totalADC = 0;
    unsigned long totalMilliVolts = 0;

    // Average multiple samples to reduce noise.
    for (int i = 0; i < TDS_SAMPLES; i++)
    {
        totalADC += analogRead(TDS_PIN);
        totalMilliVolts += analogReadMilliVolts(TDS_PIN);
        delay(2);
    }

    tdsRawADC = totalADC / (float)TDS_SAMPLES;
    tdsVoltage =
        (totalMilliVolts / (float)TDS_SAMPLES) / 1000.0f;

    // Use the 4-in-1 temperature if a packet has been received;
    // otherwise, use the formula's 25 C reference temperature.
    float waterTemperature = sensorReceived ? temperatureC : 25.0f;

    // Common approximate temperature compensation coefficient.
    float compensationCoefficient =
        1.0f + 0.02f * (waterTemperature - 25.0f);

    // Guard against an invalid coefficient if the temperature data is bad.
    if (compensationCoefficient < 0.1f)
    {
        compensationCoefficient = 1.0f;
    }

    float compensationVoltage = tdsVoltage / compensationCoefficient;

    // Common analog TDS-meter polynomial. This is an estimate and must
    // be calibrated against a known solution before scientific use.
    float calculatedTDS =
        (133.42f * compensationVoltage * compensationVoltage * compensationVoltage
         - 255.86f * compensationVoltage * compensationVoltage
         + 857.39f * compensationVoltage) * 0.5f;

    if (calculatedTDS < 0.0f)
    {
        calculatedTDS = 0.0f;
    }

    // The stated sensor range is 0-1000 ppm. Clamp display estimate to it.
    if (calculatedTDS > 1000.0f)
    {
        calculatedTDS = 1000.0f;
    }

    tdsValue = calculatedTDS;

    Serial.print("TDS ADC: ");
    Serial.print(tdsRawADC, 1);
    Serial.print(" | TDS voltage: ");
    Serial.print(tdsVoltage, 3);
    Serial.print(" V | Estimated TDS: ");
    Serial.print(tdsValue, 1);
    Serial.println(" ppm");
}

// =====================================================
// WEB ROOT
// =====================================================

void handleRoot()
{
    server.send_P(
        200,
        "text/html",
        MAIN_PAGE
    );
}

// =====================================================
// JSON DATA API
// =====================================================

void handleData()
{
    String json = "{";

    json += "\"ph\":";
    json += String(phValue, 2);

    json += ",";

    json += "\"water\":";
    json += String(waterLevel);

    json += ",";

    json += "\"light\":";
    json += String(lightValue);

    json += ",";

    json += "\"temperature\":";
    json += String(temperatureC, 2);

    json += ",";

    json += "\"turbidity\":";
    json += String(turbidityRaw, 2);

    json += ",";

    json += "\"tds\":";
    json += String(tdsValue, 2);

    json += ",";

    json += "\"sensor_connected\":";
    json += sensorReceived ? "true" : "false";

    json += "}";

    server.send(
        200,
        "application/json",
        json
    );
}

// =====================================================
// STATUS API
// =====================================================

void handleStatus()
{
    String json = "{";

    json += "\"wifi\":\"";
    json += WIFI_SSID;
    json += "\",";

    json += "\"ip\":\"";
    json += WiFi.softAPIP().toString();
    json += "\",";

    json += "\"sensor_connected\":";
    json += sensorReceived ? "true" : "false";

    json += "}";

    server.send(
        200,
        "application/json",
        json
    );
}