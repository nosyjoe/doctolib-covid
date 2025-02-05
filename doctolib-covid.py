import os
import datetime
import requests
import smtplib, ssl

DISABLE_EMAIL = os.environ.get("DISABLE_EMAIL")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

with open('centers.txt') as centers_txt:
    centers = centers_txt.readlines()
centers = [center.strip() for center in centers
           if not center.startswith("#")] 

for center in centers:

    # print(f"https://www.doctolib.de/booking/{center}.json")
    uri = "https://www.doctolib.de/booking/%s.json" % center
    data = requests.get(uri).json()["data"]
    

    # print(data["visit_motives"])
    
    visit_motives = [visit_motive for visit_motive in data["visit_motives"]
                     if visit_motive["name"].startswith("Erstimpfung Covid")]
    if not visit_motives:
        continue
    
    places = [place for place in data["places"]]
    if not places:
        continue
    
    for place in places:
        
        start_date = datetime.datetime.today().date().isoformat()
        visit_motive_ids = visit_motives[0]["id"]
        practice_ids = place["practice_ids"][0]
        place_name = place["formal_name"]
        place_address = place["full_address"]
        
        agendas = [agenda for agenda in data["agendas"]
                   if agenda["practice_id"] == practice_ids and
                   not agenda["booking_disabled"] and
                   visit_motive_ids in agenda["visit_motive_ids"]]
        if not agendas:
            continue
        
        agenda_ids = "-".join([str(agenda["id"]) for agenda in agendas])
               
        # print(visit_motive_ids)
        # print(practice_ids)
        # print(agenda_ids)
        
        params = {
                "start_date": start_date,
                "visit_motive_ids": visit_motive_ids,
                "agenda_ids": agenda_ids,
                "practice_ids": practice_ids,
                "insurance_sector": "public",
                "destroy_temporary": "true",
                "limit":2
        }
        # print(params)
        
        response = requests.get(
                "https://www.doctolib.de/availabilities.json",
                params = params,
                headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
        )
        response.raise_for_status()
        # print(response)
        
        nb_availabilities = response.json()["total"]
        
        result = str(nb_availabilities) + " appointments available at " + place_name + " - " + place_address
        print(result)
        
        if nb_availabilities > 0 and DISABLE_EMAIL != "true":
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context = context) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, result.encode('utf-8'))
                print("  --> Alert sent to " + RECEIVER_EMAIL)