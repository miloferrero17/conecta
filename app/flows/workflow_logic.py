def ejecutar_nodo(nodo_id, variables):
    NODOS = {
        500: nodo_500,
        }
    return NODOS[nodo_id](variables)


def nodo_500(variables):    
    import app.services.brain as brain
    import json

    tx = variables["tx"]
    #ctt = variables["ctt"]
    #contacto = ctt.get_by_phone(numero_limpio)
    qs = variables["qs"]
    msj = variables["msj"]
    ev = variables["ev"]

    numero_limpio = variables["numero_limpio"]
    conversation_str = variables["conversation_str"]
    #print(conversation_str)
    conversation_history = json.loads(conversation_str) if conversation_str else []



    ### clarity block
    id_question = msj.get_latest_question_id_by_phone_and_event_id(numero_limpio,2)


    print(id_question)
    question_name = qs.get_question_name_by_id(id_question)
    print(question_name)
    next_question_id = id_question + 1
    next_question_name = qs.get_question_name_by_id(next_question_id)

    
    if id_question == 0:
        conversation_history.append({
            "role": "assistant",
            "content": next_question_name
        })
        print(next_question_name)
        response_text = brain.ask_openai(conversation_history)        


        return {
            "nodo_destino": 500,
            "subsiguiente": 1,
            "conversation_str": variables.get("conversation_str", ""),
            "response_text": response_text,
            "group_id": 1,
            "question_id": (id_question+1),
            "result": "Abierta"
            }

    elif id_question != 0:
        print(question_name)
        respuesta_clara_prompt = [{"role": "assistant", "content": "Basado en este historial"+conversation_str+". El usuario contesta de forma certera la siguiente pregunta: "+question_name+". Si fue certera respondeme 1, caso contrario 0."}]
        clara = brain.ask_openai(respuesta_clara_prompt)
        print(clara)
        return {
            "nodo_destino": 500,
            "subsiguiente": 1,
            "conversation_str": variables.get("conversation_str", ""),
            "response_text": response_text,
            "group_id": 1,
            "question_id": (id_question+1),
            "result": "Abierta"
            }



'''
    ### has_answered_yet block
    next_question_id = id_question + 1
    next_question_name = qs.get_question_name_by_id(next_question_id)
    print(next_question_name)
    has_answered_yet_prompt = [{"role": "assistant", "content": "Basado en este historial"+conversation_str+". El usuario contesta de forma certera la siguiente pregunta: "+next_question_name+". Si fue certera respondeme 1, caso contrario 0."}]
    has_answered_yet = brain.ask_openai(has_answered_yet_prompt)
    print(has_answered_yet)
    print()



    




    
    
    if clara == "1":
        if (ev.get_cant_preguntas_by_event_id(2)) == id_question:
            print("Fin")
        
    
    
    
    
    if clara == "1":    
        if (ev.get_cant_preguntas_by_event_id(2)) == id_question:
            # Si estamos en la última pregunta, ir a la penúltima
            next_question = "Terminá con las preguntas"
        
            conversation_history.append({
                "role": "assistant",
                "content": next_question
            })
            print(next_question)
            response_text = brain.ask_openai(conversation_history)

            return {
                "nodo_destino": 500,
                "subsiguiente": 1,
                "conversation_str": variables.get("conversation_str", ""),
                "response_text": response_text,
                "group_id": 1,
                "question_id": id_question,
                "result": "Cerrada"
            }
        elif not id_question:
            # Si id_question no está definido o es 0/None, empezar en 1
            id_question = 1
        else:
            # En cualquier otro caso, avanzar a la siguiente pregunta
            id_question += 1

        next_question = "Proxima pregunta:" + qs.get_question_name_by_id(id_question)


        conversation_history.append({
            "role": "assistant",
            "content": next_question
        })
        print(next_question)

        response_text = brain.ask_openai(conversation_history)
        return {
            "nodo_destino": 500,
            "subsiguiente": 1,
            "conversation_str": variables.get("conversation_str", ""),
            "response_text": response_text,
            "group_id": 1,
            "question_id": id_question,
            "result": "Abierta"
        }
    
    else:
        id_question = msj.get_penultimate_question_id_by_phone(numero_limpio)        
        
        if not id_question:
            # Si id_question no está definido o es 0/None, empezar en 1
            id_question = 1
        else:
            # En cualquier otro caso, avanzar a la siguiente pregunta
            id_question += 1
        
        id_question = id_question - 1

        next_question = "Me quedaron dudas de la ultima pregunta: " + qs.get_question_name_by_id(id_question)

        conversation_history.append({
            "role": "assistant",
            "content": next_question
        })
        print(next_question)
        
        response_text = brain.ask_openai(conversation_history)
        
        return {
            "nodo_destino": 500,
            "subsiguiente": 1,
            "conversation_str": variables.get("conversation_str", ""),
            "response_text": response_text,
            "group_id": 1,
            "question_id": id_question,
            "result": "Abierta"
        }
        
'''