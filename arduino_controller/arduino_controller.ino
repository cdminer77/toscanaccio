/**
 * Toscanaccio H24 - Arduino Controller for 3 Automated Doors & Microwave
 * Handles:
 *  - Door 1: Microwave (Lock, Piston, Reed Sensor, 230V Presa Relay, Buzzer)
 *  - Door 2: Hot Water (Lock, Piston, Reed Sensor, Bianchi button relay)
 *  - Door 3: Pyrex Return (Lock, Piston, Reed Sensor)
 */

// Output Pins
const int PIN_MICROWAVE_RELAY = 2; // Presa 230V Microonde
const int PIN_LOCK_1 = 3;          // Serratura solenoide Sportello 1 (Microonde)
const int PIN_LOCK_2 = 4;          // Serratura solenoide Sportello 2 (Acqua Calda)
const int PIN_LOCK_3 = 5;          // Serratura solenoide Sportello 3 (Resi Pyrex)
const int PIN_PISTON_1 = 6;        // Attuatore/Pistone 1
const int PIN_PISTON_2 = 7;        // Attuatore/Pistone 2
const int PIN_PISTON_3 = 8;        // Attuatore/Pistone 3
const int PIN_BUZZER = 12;         // Buzzer allarmi
const int PIN_HOT_WATER_RELAY = 13;// Relè parallelo pulsante erogazione Bianchi Lei 900

// Input Pins (Reed sensors normally closed when door is locked)
const int PIN_REED_1 = 9;          // Finecorsa Sportello 1
const int PIN_REED_2 = 10;         // Finecorsa Sportello 2
const int PIN_REED_3 = 11;         // Finecorsa Sportello 3

// States
bool lastReedState1 = HIGH;
bool lastReedState2 = HIGH;
bool lastReedState3 = HIGH;

// Buzzer management variables (non-blocking)
bool buzzerActive = False;
unsigned long lastBuzzerToggle = 0;
bool buzzerState = LOW;
const int BUZZER_INTERVAL = 300; // Beep ogni 300 ms

// Bianchi button pulse variable
bool pulseHotWater = False;
unsigned long hotWaterPulseStart = 0;

void setup() {
  Serial.begin(9600);
  
  // Setup Outputs
  pinMode(PIN_MICROWAVE_RELAY, OUTPUT);
  pinMode(PIN_LOCK_1, OUTPUT);
  pinMode(PIN_LOCK_2, OUTPUT);
  pinMode(PIN_LOCK_3, OUTPUT);
  pinMode(PIN_PISTON_1, OUTPUT);
  pinMode(PIN_PISTON_2, OUTPUT);
  pinMode(PIN_PISTON_3, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_HOT_WATER_RELAY, OUTPUT);
  
  // Set default states (LOW/OFF)
  digitalWrite(PIN_MICROWAVE_RELAY, LOW);
  digitalWrite(PIN_LOCK_1, LOW);
  digitalWrite(PIN_LOCK_2, LOW);
  digitalWrite(PIN_LOCK_3, LOW);
  digitalWrite(PIN_PISTON_1, LOW);
  digitalWrite(PIN_PISTON_2, LOW);
  digitalWrite(PIN_PISTON_3, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_HOT_WATER_RELAY, LOW);
  
  // Setup Inputs (with internal pullups)
  pinMode(PIN_REED_1, INPUT_PULLUP);
  pinMode(PIN_REED_2, INPUT_PULLUP);
  pinMode(PIN_REED_3, INPUT_PULLUP);
  
  // Read initial states
  lastReedState1 = digitalRead(PIN_REED_1);
  lastReedState2 = digitalRead(PIN_REED_2);
  lastReedState3 = digitalRead(PIN_REED_3);
  
  // Print startup ready
  Serial.println("ARDUINO READY - TOSCANACCIO H24 DOORS");
  sendStatusReport();
}

void loop() {
  // 1. Leggi comandi seriali
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    parseCommand(cmd);
  }
  
  // 2. Monitora i sensori Reed e trasmetti i cambiamenti di stato
  checkReedSensors();
  
  // 3. Gestione del Beep intermittente del buzzer
  handleBuzzer();
  
  // 4. Gestione impulso relè erogazione Bianchi
  handleHotWaterPulse();
  
  delay(10);
}

void parseCommand(String cmd) {
  if (cmd == "O1") {
    // Sblocca serratura e spingi pistone sportello 1
    digitalWrite(PIN_LOCK_1, HIGH); 
    digitalWrite(PIN_PISTON_1, HIGH);
    Serial.println("S1:O");
  } else if (cmd == "C1") {
    // Retrai pistone e blocca serratura sportello 1
    digitalWrite(PIN_PISTON_1, LOW);
    digitalWrite(PIN_LOCK_1, LOW);
    Serial.println("S1:C");
  } else if (cmd == "O2") {
    digitalWrite(PIN_LOCK_2, HIGH);
    digitalWrite(PIN_PISTON_2, HIGH);
    Serial.println("S2:O");
  } else if (cmd == "C2") {
    digitalWrite(PIN_PISTON_2, LOW);
    digitalWrite(PIN_LOCK_2, LOW);
    Serial.println("S2:C");
  } else if (cmd == "O3") {
    digitalWrite(PIN_LOCK_3, HIGH);
    digitalWrite(PIN_PISTON_3, HIGH);
    Serial.println("S3:O");
  } else if (cmd == "C3") {
    digitalWrite(PIN_PISTON_3, LOW);
    digitalWrite(PIN_LOCK_3, LOW);
    Serial.println("S3:C");
  } else if (cmd == "M1") {
    // Accendi presa microonde
    digitalWrite(PIN_MICROWAVE_RELAY, HIGH);
    Serial.println("M_RELAY:ON");
  } else if (cmd == "M0") {
    // Spegni presa microonde
    digitalWrite(PIN_MICROWAVE_RELAY, LOW);
    Serial.println("M_RELAY:OFF");
  } else if (cmd == "B1") {
    // Attiva buzzer intermittente
    buzzerActive = true;
    Serial.println("BUZZER:ACTIVE");
  } else if (cmd == "B0") {
    // Spegni buzzer
    buzzerActive = false;
    digitalWrite(PIN_BUZZER, LOW);
    Serial.println("BUZZER:OFF");
  } else if (cmd == "HW") {
    // Avvia impulso erogazione acqua calda Bianchi
    pulseHotWater = true;
    hotWaterPulseStart = millis();
    digitalWrite(PIN_HOT_WATER_RELAY, HIGH);
    Serial.println("HW_PULSE:START");
  } else if (cmd == "R") {
    // Comando RESET di emergenza
    resetAll();
    Serial.println("RESET:OK");
  } else if (cmd == "STATUS") {
    sendStatusReport();
  }
}

void resetAll() {
  digitalWrite(PIN_MICROWAVE_RELAY, LOW);
  digitalWrite(PIN_LOCK_1, LOW);
  digitalWrite(PIN_LOCK_2, LOW);
  digitalWrite(PIN_LOCK_3, LOW);
  digitalWrite(PIN_PISTON_1, LOW);
  digitalWrite(PIN_PISTON_2, LOW);
  digitalWrite(PIN_PISTON_3, LOW);
  digitalWrite(PIN_BUZZER, LOW);
  digitalWrite(PIN_HOT_WATER_RELAY, LOW);
  buzzerActive = false;
  pulseHotWater = false;
}

void checkReedSensors() {
  // HIGH = Aperto (Pullup disconnesso dal magnete), LOW = Chiuso (Magnete vicino)
  bool r1 = digitalRead(PIN_REED_1);
  bool r2 = digitalRead(PIN_REED_2);
  bool r3 = digitalRead(PIN_REED_3);
  
  if (r1 != lastReedState1) {
    lastReedState1 = r1;
    Serial.print("S1:");
    Serial.println(r1 == HIGH ? "O" : "C");
  }
  
  if (r2 != lastReedState2) {
    lastReedState2 = r2;
    Serial.print("S2:");
    Serial.println(r2 == HIGH ? "O" : "C");
  }
  
  if (r3 != lastReedState3) {
    lastReedState3 = r3;
    Serial.print("S3:");
    Serial.println(r3 == HIGH ? "O" : "C");
  }
}

void handleBuzzer() {
  if (!buzzerActive) return;
  
  unsigned long currentMillis = millis();
  if (currentMillis - lastBuzzerToggle >= BUZZER_INTERVAL) {
    lastBuzzerToggle = currentMillis;
    buzzerState = !buzzerState;
    digitalWrite(PIN_BUZZER, buzzerState ? HIGH : LOW);
  }
}

void handleHotWaterPulse() {
  if (!pulseHotWater) return;
  
  unsigned long currentMillis = millis();
  // Durata dell'impulso relè: 1.0 secondi
  if (currentMillis - hotWaterPulseStart >= 1000) {
    pulseHotWater = false;
    digitalWrite(PIN_HOT_WATER_RELAY, LOW);
    Serial.println("HW_PULSE:END");
  }
}

void sendStatusReport() {
  Serial.print("S1:"); Serial.println(digitalRead(PIN_REED_1) == HIGH ? "O" : "C");
  Serial.print("S2:"); Serial.println(digitalRead(PIN_REED_2) == HIGH ? "O" : "C");
  Serial.print("S3:"); Serial.println(digitalRead(PIN_REED_3) == HIGH ? "O" : "C");
  Serial.print("M_RELAY:"); Serial.println(digitalRead(PIN_MICROWAVE_RELAY) == HIGH ? "ON" : "OFF");
  Serial.print("BUZZER:"); Serial.println(buzzerActive ? "ACTIVE" : "OFF");
}
