import logging
import threading
import time
import os
from typing import Dict, Callable, Optional

logger = logging.getLogger("toscanaccio.hardware")

# Import serial with fallback to Mock mode
SERIAL_AVAILABLE = False
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    logger.warning("Libreria 'pyserial' non installata. L'hardware manager funzionerà in modalità MOCK.")

class HardwareManager:
    def __init__(self):
        self.com_port = os.getenv("ARDUINO_PORT", "COM3")
        self.baud_rate = 9600
        self.serial_conn = None
        self.connection_status = "DISCONNECTED"
        self.lock = threading.Lock()
        
        # State variables
        self.door_states: Dict[int, str] = {1: "CLOSED", 2: "CLOSED", 3: "CLOSED"}
        self.microwave_relay = False
        
        # Active microwave timer tracking
        self.microwave_time_left = 0
        self.microwave_timer_thread: Optional[threading.Thread] = None
        self.timer_stop_event = threading.Event()
        
        # Notification callbacks (e.g., to trigger vocal alerts in the browser or via API logs)
        self.vocal_callback: Optional[Callable[[str], None]] = None
        self.status_change_callback: Optional[Callable[[], None]] = None
        
        self.read_thread = None
        self.keep_reading = False
        
        # Inizializza la connessione
        self.connect()

    def connect(self):
        if not SERIAL_AVAILABLE:
            self.connection_status = "MOCKED"
            logger.info("HardwareManager inizializzato in modalità MOCK (Libreria non presente).")
            return

        try:
            with self.lock:
                self.serial_conn = serial.Serial(
                    port=self.com_port,
                    baudrate=self.baud_rate,
                    timeout=1.0
                )
                self.connection_status = "CONNECTED"
                self.keep_reading = True
                self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
                self.read_thread.start()
                logger.info(f"Connesso all'Arduino sulla porta {self.com_port}.")
        except Exception as e:
            self.connection_status = "MOCKED"
            logger.error(f"Impossibile connettersi ad Arduino su {self.com_port}: {e}. Avvio in modalità MOCK.")

    def disconnect(self):
        self.keep_reading = False
        if self.read_thread:
            self.read_thread.join(timeout=1.0)
        with self.lock:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            self.serial_conn = None
            if self.connection_status != "MOCKED":
                self.connection_status = "DISCONNECTED"

    def reset_connection(self):
        logger.info("Ripristino della connessione hardware...")
        self.disconnect()
        self.connect()
        self.send_command("R") # Send Reset to Arduino

    def send_command(self, cmd: str):
        """Invia un comando sulla seriale o simula l'invio in modalità MOCK"""
        cmd_string = f"{cmd}\n"
        if self.connection_status == "CONNECTED" and self.serial_conn:
            try:
                with self.lock:
                    self.serial_conn.write(cmd_string.encode('ascii'))
                    logger.debug(f"[Hardware TX] {cmd}")
            except Exception as e:
                logger.error(f"Errore di scrittura sulla seriale: {e}")
                self.connection_status = "MOCKED"
        else:
            logger.info(f"[Hardware MOCK TX] Invio comando simulato: {cmd}")
            # Simula le risposte dell'Arduino in modalità Mock
            self._handle_mock_response(cmd)

    def _read_loop(self):
        """Thread che legge continuamente i dati inviati da Arduino"""
        buffer = ""
        while self.keep_reading:
            if not self.serial_conn or not self.serial_conn.is_open:
                time.sleep(0.5)
                continue
            try:
                if self.serial_conn.in_waiting > 0:
                    data = self.serial_conn.read(self.serial_conn.in_waiting).decode('ascii', errors='ignore')
                    buffer += data
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if line:
                            self._parse_line(line)
            except Exception as e:
                logger.error(f"Errore nella lettura seriale: {e}")
                time.sleep(1)
            time.sleep(0.05)

    def _parse_line(self, line: str):
        """Interpreta le stringhe inviate da Arduino"""
        logger.debug(f"[Hardware RX] {line}")
        
        # Esempi di risposte di stato: S1:O, S1:C, S2:O, S2:C, S3:O, S3:C
        if line.startswith("S") and ":" in line:
            try:
                parts = line.split(":")
                door_num = int(parts[0][1:])
                state = "OPEN" if parts[1] == "O" else "CLOSED"
                
                old_state = self.door_states.get(door_num)
                self.door_states[door_num] = state
                
                if old_state != state:
                    logger.info(f"Stato Sportello {door_num} cambiato a: {state}")
                    if self.status_change_callback:
                        self.status_change_callback()
            except Exception as e:
                logger.error(f"Errore nel parsing dello stato dello sportello: {e}")

    def _handle_mock_response(self, cmd: str):
        """Simula la risposta fisica dell'Arduino per il mock"""
        if cmd == "O1":
            self.door_states[1] = "OPEN"
        elif cmd == "C1":
            self.door_states[1] = "CLOSED"
        elif cmd == "O2":
            self.door_states[2] = "OPEN"
        elif cmd == "C2":
            self.door_states[2] = "CLOSED"
        elif cmd == "O3":
            self.door_states[3] = "OPEN"
        elif cmd == "C3":
            self.door_states[3] = "CLOSED"
        elif cmd == "M1":
            self.microwave_relay = True
        elif cmd == "M0":
            self.microwave_relay = False
        elif cmd == "R":
            self.door_states = {1: "CLOSED", 2: "CLOSED", 3: "CLOSED"}
            self.microwave_relay = False
            
        if self.status_change_callback:
            self.status_change_callback()

    # --- Comandi Pubblici degli Sportelli ---
    
    def open_door(self, door_id: int):
        if door_id in [1, 2, 3]:
            logger.info(f"Comando di APERTURA sportello {door_id}")
            self.send_command(f"O{door_id}")
            
    def close_door(self, door_id: int):
        if door_id in [1, 2, 3]:
            logger.info(f"Comando di CHIUSURA sportello {door_id}")
            self.send_command(f"C{door_id}")

    def set_microwave_power(self, state: bool):
        self.microwave_relay = state
        self.send_command("M1" if state else "M0")

    def trigger_hot_water_credit(self):
        """Invia un impulso o comando per erogare acqua calda"""
        logger.info("Autorizzazione acqua calda (Bianchi Lei 900)...")
        self.send_command("HW")

    # --- Gestione del Timer Vocale e Buzzer del Microonde ---

    def start_microwave_cycle(self, duration_seconds: int = 180):
        """Avvia il ciclo del microonde in un thread separato"""
        self.stop_microwave_cycle()
        
        self.timer_stop_event.clear()
        self.microwave_time_left = duration_seconds
        
        self.microwave_timer_thread = threading.Thread(
            target=self._microwave_timer_loop, 
            args=(duration_seconds,),
            daemon=True
        )
        self.microwave_timer_thread.start()

    def stop_microwave_cycle(self):
        """Forza lo spegnimento immediato del microonde"""
        self.timer_stop_event.set()
        if self.microwave_timer_thread:
            self.microwave_timer_thread.join(timeout=1.0)
            self.microwave_timer_thread = None
        self.set_microwave_power(False)
        self.microwave_time_left = 0

    def _microwave_timer_loop(self, total_seconds: int):
        logger.info(f"Inizio riscaldamento microonde: {total_seconds} secondi.")
        
        self.open_door(1)
        self._say_vocal("Sportello sbloccato. Inserisci il piatto e chiudi lo sportello per iniziare.")
        
        # Attendi 8 secondi per dare il tempo di inserire e chiudere lo sportello
        time.sleep(8)
        
        # Controlla se lo sportello è chiuso
        wait_start = time.time()
        while self.door_states[1] == "OPEN" and (time.time() - wait_start) < 30:
            if self.timer_stop_event.is_set():
                return
            time.sleep(1)
            
        if self.door_states[1] == "OPEN":
            self._say_vocal("Tempo scaduto. Sportello non chiuso. Riscaldamento annullato.")
            self.close_door(1)
            return

        self.close_door(1)
        self.set_microwave_power(True)
        self._say_vocal("Riscaldamento avviato. Durata tre minuti.")
        
        buzzer_active = False
        
        while self.microwave_time_left > 0:
            if self.timer_stop_event.is_set():
                break
                
            time.sleep(1)
            self.microwave_time_left -= 1
            
            if self.microwave_time_left == 30:
                self._say_vocal("Attenzione: mancano trenta secondi al termine del riscaldamento.")
                self.send_command("B1") # B1 = Avvia buzzer intermittente
                buzzer_active = True
                
            if self.status_change_callback:
                self.status_change_callback()

        self.set_microwave_power(False)
        if buzzer_active:
            self.send_command("B0") # B0 = Spegni buzzer
            
        if not self.timer_stop_event.is_set():
            self._say_vocal("Riscaldamento completato. Preleva il piatto con cautela.")
            self.open_door(1)
            
            time.sleep(15)
            self.close_door(1)
            self._say_vocal("Grazie e buon appetito da Toscanaccio!")
        else:
            self._say_vocal("Riscaldamento terminato manualmente.")
            self.open_door(1)

        self.microwave_time_left = 0
        if self.status_change_callback:
            self.status_change_callback()

    def _say_vocal(self, message: str):
        logger.info(f"[VIRTUAL ME VOCALE]: {message}")
        if self.vocal_callback:
            try:
                self.vocal_callback(message)
            except Exception:
                pass
        
        # Sintesi vocale nativa Windows tramite PowerShell (SpeechSynthesis)
        try:
            import subprocess
            # Escapiamo gli apici singoli per PowerShell
            escaped_msg = message.replace("'", "''")
            ps_cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{escaped_msg}')"
            subprocess.Popen(["powershell", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error(f"Errore durante la riproduzione vocale nativa: {e}")

# Istanza singleton globale
hardware_manager = HardwareManager()
