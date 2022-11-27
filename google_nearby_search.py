# this file provides functions to parse data from the Google Places API nearby search
# part 1 provides a workaround for the 60 query limit by recursively splitting circles into 4 smaller circles
# part 2 categorizes by place type into land use based on NAICS categorization

import requests, json
import time
import csv
import math


# part 1: extract data for a region from the API and save it into a csv


def query_category(lat,long,radius,category,all_pois,category_count=0):
    """
    performs a query request from a category with coords lat,long and radius (in meters)
    """
    count=0
    api_key = ###insert
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    initial_url = url + '?location=' + str(lat)+'%2C'+str(long) + '&radius=' + str(radius) + '&type=' + category + '&key=' + api_key
    
    #first request
    request=requests.get(initial_url).json()
    #looping through the pages:
    while request.get('next_page_token',False):
        status=request['status']
        if status!='OK' and status!='ZERO_RESULTS':
            print('error')
        results=request['results']
        for result in results:
            all_pois.add(get_data(result))
            count+=1
        time.sleep(2)
        next_page=request.get('next_page_token',False)
        request = requests.get(initial_url + '&pagetoken=' + next_page).json()
    #last page
    status=request['status']
    if status!='OK' and status!='ZERO_RESULTS':
        print('error')
    results=request['results']
    for result in results:
        all_pois.add(get_data(result))
        count+=1

    #add to total
    category_count+=count

    #if reached limit (60 queries), recursively query 4 smaller circles
    if count==60:
        delta_lat=radius/(math.sqrt(8)*111120)
        delta_long=radius/(math.sqrt(8)*111319.488*math.cos(lat*math.pi/180))
        #1 degree latitude=111,120 meters, 1 degree longitude=111,319.488*cos(latitude) meters
        all_pois,category_count=query_category(lat+delta_lat,long+delta_long,radius/2,category,all_pois,category_count)
        all_pois,category_count=query_category(lat+delta_lat,long-delta_long,radius/2,category,all_pois,category_count)
        all_pois,category_count=query_category(lat-delta_lat,long+delta_long,radius/2,category,all_pois,category_count)
        all_pois,category_count=query_category(lat-delta_lat,long-delta_long,radius/2,category,all_pois,category_count)

    return all_pois,category_count


def get_data(result):
    """
    takes a result from the results section of an API request and returns a tuple of the fields we want
    """
    name=result.get('name',None),
    lat=result.get('geometry',None).get('location',None).get('lat',None),
    long=result.get('geometry',None).get('location',None).get('lng',None),
    types=tuple(result.get('types',None))
    return name+lat+long+(types,)


def nearby_search(place,lat,long,radius=1138):
    """
    input: place (str name of place we want to search around), coordinates lat and long, radius (number in meters, default circumcircle of 1x1 mile square is 1138m)
    """
    categories={'accounting','airport','amusement_park','aquarium','art_gallery','atm','bakery','bank','bar','beauty_salon','bicycle_store','book_store','bowling_alley','bus_station',
                'cafe','campground','car_dealer','car_rental','car_repair','car_wash','casino','cemetery','church','city_hall','clothing_store','convenience_store','courthouse','dentist',
                'department_store','doctor','drugstore','electrician','electronics_store','embassy','fire_station','florist','funeral_home','furniture_store','gas_station','gym','hair_care',
                'hardware_store','hindu_temple','home_goods_store','hospital','insurance_agency','jewelry_store','laundry','lawyer','library','light_rail_station','liquor_store',
                'local_government_office','locksmith','lodging','meal_delivery','meal_takeaway','mosque','movie_rental','movie_theater','moving_company','museum','night_club','painter',
                'park','parking','pet_store','pharmacy','physiotherapist','plumber','police','post_office','primary_school','real_estate_agency','restaurant','roofing_contractor','rv_park',
                'school','secondary_school','shoe_store','shopping_mall','spa','stadium','storage','store','subway_station','supermarket','synagogue','taxi_stand','tourist_attraction',
                'train_station','transit_station','travel_agency','university','veterinary_care','zoo',}
    all_pois=set()
    
    for category in categories:
        category_count=query_category(lat,long,radius,category,all_pois)[1]
        print(f'{category_count} points in {category} category')
    
    #save as csv file
    labels=['name','lat','lng','types']
    data=[poi for poi in all_pois]
    with open(f'{place}_{radius}.csv','w') as file:
        writer = csv.writer(file)
        writer.writerow(labels)
        for poi_data in data:
            writer.writerow(poi_data)


# part 2: categorize data into land use type based on 'type' from Google API


def frequent_types(file):
    """
    returns a sorted list of the most common types in a file and their frequencies (tuple)
    """
    frequencies={}
    with open(file,'r') as file:
        reader = csv.reader(file)
        for row in reader:
            types=row[3][2:-2].split("', '")
            for t in types:
                if t not in frequencies:
                    frequencies[t]=1
                else:
                    frequencies[t]+=1
    return sorted(frequencies.items(), key=lambda kv:kv[1], reverse=True)


def clean(file,mapping):
    """
    creates a new file containing only the types that we are interested in
    """
    with open(file,'r') as file1:
        reader = csv.reader(file1)
        with open(f'{file[:-4]}_cleaned.csv', 'w') as file2:
            writer = csv.writer(file2)
            writer.writerow(next(reader)[:3]+['relevant_types',])
            #writer.writerow(next(reader)[:3]+['relevant_types','ancillary_types',])
            for row in reader:
                types=row[3][2:-2].split("', '")
                relevant_types=set()
                #ancillary_types=set()
                for t in types:
                    if t in mapping.keys():
                        relevant_types.add(t)
                    #else:
                        #ancillary_types.add(t)
                writer.writerow(row[:3]+[relevant_types,])
                #writer.writerow(row[:3]+[relevant_types,ancillary_types,])


def _mapping(categorization):
    """
    produce a mapping of type to category based on categorizations
    """
    mapping={}
    for k,v in categorization.items():
        for type in v:
            mapping[type]=k
    return mapping

  
def categorize(file,mapping):
    """
    takes a cleaned file and (using the same mapping that was used to clean) assigns categories in a new column
    """
    with open(file,'r') as file1:
        reader = csv.reader(file1)
        with open(f'{file[:-12]}_categorized.csv', 'w') as file2:
            writer = csv.writer(file2)
            writer.writerow(next(reader)+['categories'])
            for row in reader:
                types=row[3][2:-2].split("', '")
                categories=set()
                for t in types:
                    categories.add(mapping[t])
                writer.writerow(row+[categories])



##nearby_search('central_square',42.365128734069586,-71.10254858759215,285)
##nearby_search('lexington_green',42.44965384516684,-71.23077273099918)
##nearby_search('downtown_concord',42.45985044479248, -71.35018790206628)

##NAICS_categorization={'72':{'bakery','restaurant','cafe','meal_delivery','meal_takeaway','lodging',},
##                    '48-49':{'bus_station','train_station','transit_station','taxi_stand','parking','gas_station','light_rail_station','subway_station','airport','car_rental','travel_agency','storage' ,'car_repair','car_dealer','moving_company',},
##                    '44-45':{'shoe_store','shopping_mall','department_store','home_goods_store','hardware_store','bicycle_store','jewelry_store','clothing_store','furniture_store','liquor_store','store','electronics_store','florist','pet_store','hair_care','convenience_store','supermarket','car_wash','book_store','movie_rental',},
##                    '52':{'atm','bank','insurance_agency','accounting',},
##                    '53':{'real_estate_agency',},
##                    '61':{'school','secondary_school','university','primary_school',},
##                    '71':{'art_gallery','movie_theater','night_club','tourist_attraction','museum','bowling_alley','casino','amusement_park','stadium','rv_park','campground','zoo','aquarium','park','bar','library',},
##                    '62':{'drugstore','pharmacy','physiotherapist','veterinary_care','dentist','hospital','doctor',},
##                    '92':{'city_hall','courthouse','local_government_office','embassy','post_office','fire_station','police',},
##                    '81':{'plumber','lawyer','electrician','cemetery','painter','locksmith','funeral_home','beauty_salon','spa','laundry','gym','roofing_contractor','church','synagogue','mosque','hindu_temple',},
##                    }
##NAICS_mapping=_mapping(NAICS_categorization)

##clean('central_square_285.csv',NAICS_mapping)
##print(frequent_types('central_square_285_cleaned.csv'))
##categorize('central_square_285_cleaned.csv',NAICS_mapping)
