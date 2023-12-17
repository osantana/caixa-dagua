# Caixa d'Água

Automação para controle de poço e caixa d'água da chácara


## Módulo central

* ESP32-WROOM rodando MicroPython
* Display TFT 2.4" 320x240 com Touch (ILI9341 + XPT2046)
* Módulo de Rádio HC-12
* RTC DS1307


### Instalação hidráulica

* Bóia automática na caixa d'água


## Módulo de controle

* Arduino Nano
* Módulo de Rádio HC-12
* Módulo de Relés 4 canais


### Instalação hidráulica

* Válvula eletrica 3 vias 220V
* Bomba hidráulica 220V


# Protocolo de comunicação

* SOURCE_ID: byte (0x00 = central)
* TARGET_ID: byte (0x00 = central)
* CHAIN_SIZE: byte
* CHAIN: list[byte] (devices que repassaram o pacote)
* COMMAND:
  * 0x00: RESET (reseta target)
  * 0x01: SET (seta parâmetro)
    * KEY: pascal-str
    * VALUE: pascal-str
  * 0x02: GET (recupera parâmetro)
    * KEY: pascal-str
    * VALUE: pascal-str
  * 0x03: RESPONSE (parâmetro recuperado)
    * KEY: pascal-str
    * VALUE: pascal-str
  * 0x04: NOTIFY (notificação)
    * PRIORITY: byte
    * NOTIFICATION: pascal-str

  * 0x11: READ
    * SENSOR_ID: byte (número do sensor para ler)
  * 0x12: INFO
    * SENSOR_ID: byte (número do sensor lido)
    * DATA: pascal-str

  * 0x20: START:
    * CHANNEL: byte (número do canal a ser parado)
    * TIMEOUT: uint (número de segundos de funcionamento deve ser diferente de 0)
  * 0x21: STOP (parada forçada. só deve ser usado em emergência)
    * CHANNEL: byte (número do canal a ser parado. 0xFF = todos)

* PARAMETERS: (dependente do comando)
* CHECKSUM: (a definir)
