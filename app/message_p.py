# message_p.py actualizado

# Módulos Build-in
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo  # Python 3.9+
from typing import Optional
import json
from dateutil.parser import isoparse
import requests
import time
import os


# Módulos de 3eros
import app.services.twilio_service as twilio
from twilio.twiml.messaging_response import MessagingResponse

# Módulos propios
from app.Model.users import Users   
from app.Model.enums import Role
from app.Model.contacts import Contacts
from app.Model.engine import Engine
from app.Model.messages import Messages
from app.Model.transactions import Transactions
from app.Model.questions import Questions
from app.Model.events import Events
from app.Utils.table_cleaner import TableCleaner
from app.flows.workflow_logic import ejecutar_nodo

import app.services.brain as brain
import app.services.uploader as uploader
import app.services.decisions as decs
from app.services.decisions import next_node_fofoca_sin_logica, limpiar_numero, calcular_diferencia_en_minutos,ejecutar_codigo_guardado
import app.services.brain as brain

def handle_incoming_message(body, to,  tiene_adjunto, media_type, file_path, transcription, description,pdf_text):
    print(body)
    #twilio.enviar_mensaje_si_no("+5491133585362")
    print(media_type)
    
    '''
    if tiene_adjunto == 1:
        if media_type.startswith("image"):
            twilio.send_whatsapp_message(description, to, None)    
        if( media_type == "application/pdf"):
            twilio.send_whatsapp_message(pdf_text, to, None)    
    '''

    msj = Messages()
    tx = Transactions()
    ev = Events()
    numero_limpio = limpiar_numero(to)
    ctt = Contacts()    

    # Obtener el timestamp actual en UTC
    now_utc = datetime.now(timezone.utc)
    formatted_now = now_utc.strftime("%Y-%m-%d %H:%M:%S.%f")

    ### 1) Inicializo las variables
    event_id = 0
    msg_key = 0
    nodo_destino = 0
    ultimo_mensaje = ""
    response_text = ""
    next_node_question = ""
    registro = 0
    max_preguntas= 0
    contexto = ""
    eng = Engine()
    aux = Messages()
    qs = Questions()
    last_assistant_question = Messages()
    group_id = 0
    question_id = 0
    question_name =""
    contacto = ""
    result = ""
    url = ""
    subsiguiente = 0
    conversation_str = ""
    conversation_history = [{"role": "system", "content": ""}]
    aux_question_fofoca = [{"role": "system", "content": ""}]


    contacto = ctt.get_by_phone(numero_limpio)



    #### 2) Alta de contacto   
    if contacto is None:
        entorno = os.getenv("ENV", "undefined")        
        if entorno == "undefined":
            event_id = 2

        
        ctt.add(
            event_id=event_id, 
            name="Juan",
            phone=numero_limpio
        )
        
        msg_key = ev.get_nodo_inicio_by_event_id(event_id)
        msj.add(
            msg_key=500,
            text="Nuevo contacto",
            phone=numero_limpio,
            event_id=event_id,
            question_id=0
        )
        
        print("1) Contacto creado")
        

    contacto = ctt.get_by_phone(numero_limpio)
    











    #### 3) Gestión de sesiones   
    if contacto is not None:        
        event_id = ctt.get_event_id_by_phone(numero_limpio)
        contexto_agente = ev.get_description_by_event_id(event_id)
        conversation_history = [{
            "role": "system",
            "content":contexto_agente
        }]
        conversation_str = json.dumps(conversation_history)

        try: #### Creacion y update de sesiones
            ultima_tx = tx.get_last_timestamp_by_phone(numero_limpio)
            if ultima_tx is None:
                tx.add(
                    contact_id=contacto.contact_id,
                    phone=numero_limpio,
                    name="Abierta",
                    event_id=event_id,
                    conversation = conversation_str,
                    timestamp=formatted_now,
                    data_created=formatted_now
                )
                print("2.4) Creo la tx")
            
            
            elif tx.is_last_transaction_closed(numero_limpio) == 1: ### Esta cerrada
                print("2.8) Sesion cerrada sin hacer nada")
                tx.add(
                    contact_id=contacto.contact_id,
                    phone=numero_limpio,
                    name="Abierta",
                    event_id=event_id,
                    conversation = conversation_str,
                    timestamp=formatted_now,
                    data_created=formatted_now
                )
                
                msg_key = ev.get_nodo_inicio_by_event_id(event_id)
                msj.add(
                    msg_key=msg_key, 
                    text=body, 
                    phone=numero_limpio,
                    event_id=event_id,
                    question_id=0
                )    
                print("2.6) Sesion nueva")
                    
            elif calcular_diferencia_en_minutos(tx, numero_limpio) > ev.get_time_by_event_id(event_id):
                                
                tx.update(
                    id=ultima_tx["id"],
                    contact_id=contacto.contact_id,
                    phone=numero_limpio,
                    name="Cerrada",
                    timestamp=formatted_now,
                    event_id=event_id
                )
                #print(tx)
                print("2.5) Sesion vencida")
            
                tx.add(
                    contact_id=contacto.contact_id,
                    phone=numero_limpio,
                    name="Abierta",
                    event_id=event_id,
                    conversation = conversation_str,
                    timestamp=formatted_now,
                    data_created=formatted_now
                )

                msg_key = ev.get_nodo_inicio_by_event_id(event_id)

                msj.add(
                    msg_key=msg_key, 
                    text=body, 
                    phone=numero_limpio,
                    event_id=event_id,
                    question_id=0

                )    
                print("2.6) Sesion nueva")
            
            else:
                ### 3) Trabajo sobre la sesión vigente/recien creada 
                print("2.7) Sesion vigente") 
        
            
            ultimo_mensaje = msj.get_latest_by_phone(numero_limpio)
            id_question = msj.get_latest_question_id_by_phone_and_event_id(numero_limpio,2)

            if ultimo_mensaje:
                msg_key = ultimo_mensaje.msg_key
                #print(ultimo_mensaje)
                #print(msg_key)
                msj.add(
                    msg_key=msg_key, 
                    text=body, 
                    phone=numero_limpio,
                    event_id=event_id,
                    question_id=id_question
                )


            # Bloque de update de sesión
            conversation_str = tx.get_open_conversation_by_contact_id(contacto.contact_id)
            #print(conversation_str)
            #print(conversation_str)
            conversation_history = json.loads(conversation_str) if conversation_str else []
            conversation_history.append({
                "role": "user",
                "content": body
            })
            conversation_str = json.dumps(conversation_history)
            
            nodo_destino = msg_key
            #print(nodo_destino)

            variables = {
                    "body": body,
                    "max_preguntas":max_preguntas,
                    "nodo_destino": nodo_destino,
                    "numero_limpio": numero_limpio,
                    "msg_key": msg_key,
                    "ctt": ctt,
                    "msj": msj,
                    "qs":qs,
                    "last_assistant_question": last_assistant_question,
                    "eng": eng,
                    "tx": tx,
                    "ev":ev,
                    "response_text": response_text,
                    "conversation_str": conversation_str,
                    "aux_question_fofoca": aux_question_fofoca,
                    "ultimo_mensaje": ultimo_mensaje,
                    "next_node_question": next_node_question,
                    "aux": aux,
                    "contacto": contacto,
                    "result": result,
                    "conversation_history": conversation_history,
                    "question_name": question_name,
                    "question_id": question_id,
                    "group_id":group_id,
                    "event_id":event_id,
                    "url":url
                }

            while True:
                print("Usted está entrando a:", nodo_destino)
                contexto_actualizado = ejecutar_nodo(nodo_destino, variables)
                variables.update(contexto_actualizado)
                #print(variables)
                # Salida del loop
                #print(variables.get("conversation_str"))
                nodo_destino = variables.get("nodo_destino")
                if variables.get("subsiguiente") == 1:
                    break
            print(variables.get("result"))
            

            conversation_history.append({
                "role": "assistant",
                "content":variables.get("response_text")
            })
            conversation_str = json.dumps(conversation_history)
            #print(conversation_str)
            
            #print(variables.get("response_text"))
            #mensaje = msj.get_latest_by_phone(numero_limpio)
            mensaje_a_enviar = variables.get("response_text") or "Hubo un problema interno. Por favor intentá más tarde."
            #twilio.send_whatsapp_message(mensaje_a_enviar, to, variables.get("url"))

            open_tx_id = tx.get_open_transaction_id_by_contact_id(contacto.contact_id)
            #print(open_tx_id)
            if variables.get("result") == "Cerrada": 
                tx.update(
                    id=open_tx_id,
                    contact_id=contacto.contact_id,
                    phone=numero_limpio,
                    name="Cerrada",
                    conversation=conversation_str,
                    timestamp=formatted_now,
                    event_id=event_id
                )
                time.sleep(2)
                #twilio.send_whatsapp_message("Fin de la consulta, gracias!", to, None)
            else:
                tx.update(
                    id=open_tx_id,
                    contact_id=contacto.contact_id,
                    phone=numero_limpio,
                    name="Abierta",
                    conversation=conversation_str,
                    timestamp=formatted_now,
                    event_id=event_id

                )
            print()
            print(variables.get("response_text"))
            
            # Cargo la ultima pregunta
            last_assistant_question.add(
                msg_key=variables.get("nodo_destino"),
                text=variables.get("response_text"),
                phone=numero_limpio,
                group_id=variables.get("group_id"),
                question_id=variables.get("question_id"),
                event_id=event_id         
            )
            return "Ok"

        except (TypeError, KeyError) as e:
            print(f"❌ Error accediendo a 'name': {e}")
