import os
import json
import tweepy
import logging
import urllib.request

AVARIAS_URL = "https://lizaqua.smas-leiria.pt/smas/avarias.php"

logger = logging.getLogger()
logging.basicConfig(filename='smas_lra.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

#twitter loggin and api creation
def create_api():
    consumer_key = os.getenv("CONSUMER_KEY_2")
    consumer_secret = os.getenv("CONSUMER_SECRET_2")
    access_token = os.getenv("ACCESS_TOKEN_2")
    access_token_secret = os.getenv("ACCESS_TOKEN_SECRET_2")

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True,
        wait_on_rate_limit_notify=True)
    try:
        api.verify_credentials()
    except Exception as e:
        logger.error("Error creating API", exc_info=True)
        raise e
    logger.info("API created")
    return api


# create report message and tweet it
def send_report(elem):
    report = ""

    # if not resolved is "in curso"
    if not str(elem['estado']).lower() == "resolvido":
        if elem['fecho'] == 1:
            report = "[%s] Na freguesia de %s, localidade %s, na %s com corte de abastecimento a partir das %s. Detalhe: %s. #SMAS_LRA_AVARIA" % (elem['estado'], elem['freguesia'], elem[
            'localidade'], elem['rua'], elem['datafecho'], elem['ocorrencia'])
        else:
            report = "[%s] Na freguesia de %s, localidade %s, na %s sem corte de abastecimento. Detalhe: %s. #SMAS_LRA_AVARIA" % (elem['estado'], elem['freguesia'], elem[
            'localidade'], elem['rua'], elem['ocorrencia'])
    #if resolved
    else:
        if elem['fecho'] == 1:
            report = "[%s] Na freguesia de %s, localidade %s, na %s com restabelecimento de água às %s. Detalhe: %s. #SMAS_LRA_AVARIA" % (elem['estado'], elem['freguesia'], elem[
            'localidade'], elem['rua'], elem['dataabertura'], elem['ocorrencia'])
        else:
            report = "[%s] Na freguesia de %s, localidade %s, na %s. Detalhe: %s. #SMAS_LRA_AVARIA" % (elem['estado'], elem['freguesia'], elem[
            'localidade'], elem['rua'], elem['ocorrencia'])

    logging.info(report)
    api = create_api()
    api.update_status(report)
    logging.debug("Tweet Sent")


def search_element_in_array(elem_actual, array):
    for elem in array:
        # if found same location on processed returns it
        if elem['freguesia'] == elem_actual['freguesia'] and elem['localidade'] == elem_actual['localidade'] and elem['rua'] == elem_actual['rua']:
            return elem
    return


def main():

    logging.info("Running 'process_occurrences.py")
    #collect current occurrences file
    urllib.request.urlretrieve(AVARIAS_URL, "avarias.json")

    # No file to be processed
    if not os.path.isfile('avarias.json'):
        logging.debug("No 'avarias.json' file found. Exiting.")
        return
    else:
        # opens file as json
        avarias_file = open('avarias.json', 'r')
        avarias_data = json.load(avarias_file)

        # If there is no processed file sends reports for all current and renames it as processed
        if not os.path.isfile('avarias_processadas.json'):
            logging.debug("No 'avarias_processadas.json' file found.")
            for elem in avarias_data['avarias']:
                send_report(elem)

            avarias_file.close()
            os.rename('avarias.json', 'avarias_processadas.json')
            return

        # if there is a processed file just needs to do diff between current and processed
        else:
            logging.debug("'avarias.json' and 'avarias_processadas.json' files found.")
            processadas_file = open('avarias_processadas.json', 'r')
            processadas_data = json.load(processadas_file)

            for elem in avarias_data['avarias']:
                result = search_element_in_array(elem, processadas_data['avarias'])
                if result:
                    # if although its same location has an updated state
                    if not (elem['estado'] == result['estado']):
                        send_report(elem)
                # otherwise its new
                else:
                    #new occurrence
                    send_report(elem)


             # Close fds and rename/remove files
            processadas_file.close()
            avarias_file.close()
            os.remove('avarias_processadas.json')
            os.rename('avarias.json', 'avarias_processadas.json')
            return


if __name__ == "__main__":
    main()