
#include <WiFi.h>
#include "data.h"

const char* ssid = "GreeNnet";
const char* password = "kolokolo";

WiFiServer server(80);

unsigned long currentTime = millis();
unsigned long previousTime = 0; 
const long timeoutTime = 2000;

void connectWlan() {
  WiFi.begin(ssid, password);
  int iters = 0;
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    if (iters > 20) {
      Serial.println("Cannot connects to Wifi");
      Serial.println(ssid);
      return;
    }
    iters++;
    delay(500);
  }
  Serial.println("");
  Serial.println("WiFi connected.");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  return;
}

void setup() {
  Serial.begin(115200);
  Serial.print("Connecting to ");
  Serial.println(ssid);
  while (WiFi.status() != WL_CONNECTED) {
    connectWlan();
  }

  server.begin();
}

void loop() {
  while (WiFi.status() != WL_CONNECTED) {
    connectWlan();
  }

  WiFiClient client = server.available();   // Listen for incoming clients

  if (client) {                             // If a new client connects,
    currentTime = millis();
    previousTime = currentTime;
    Serial.println("New Client.");          // print a message out in the serial port
    String currentLine = "";                // make a String to hold incoming data from the client
    while (client.connected() && currentTime - previousTime <= timeoutTime) {  // loop while the client's connected
      currentTime = millis();
      if (client.available()) {
        char c = client.read();             // read a byte, then
        Serial.write(c);                    // print it out the serial monitor
        // header += c;
        if (c == '\n') {    
          if (currentLine.length() == 0) {
            client.println("HTTP/1.1 200 OK");
            client.println("Content-type:text/html");
            client.println("Connection: close");
            client.println();
            client.println(cockFinderHtml);
            client.println();
            break;
          } else { // if you got a newline, then clear currentLine
            currentLine = "";
          }
        } else if (c != '\r') {  // if you got anything else but a carriage return character,
          currentLine += c;      // add it to the end of the currentLine
        }
      }
    }
    client.stop();
    Serial.println("Client disconnected.");
    Serial.println("");
  }
}
