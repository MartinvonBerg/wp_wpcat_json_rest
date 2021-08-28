import requests
import json
from distutils.version import StrictVersion
import os, sys, magic, pathlib, string, re, pprint
import datetime, pytest, base64, hashlib, time
from PIL import Image, ImageOps


# prepare the path for the import of the WP-class. VS Code doesn't detect the files therefore and shows a warning here
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
SCRIPT_DIR2 = os.path.join(SCRIPT_DIR, 'classes')
sys.path.append(SCRIPT_DIR2)
from WP_test_object import WP_EXT_REST_API, WP_REST_API
from helper_functions import find_plugin_in_json_resp_body, remove_html_tags, get_image

# define the tested site(s) which shall undergo the test.
# TODO: provide the login data by key input
wp_site1 = {
    'url' : 'https://www.mvb1.de',
    'rest_route' : '/wp-json/wp/v2',
    'user' : 'user',
    'password' : 'pwd',
    'testfolder' : 'pythontest'
}

wp_site2 = {
    'url' : 'https://www.bergreisefoto.de/wordpress',
    'rest_route' : '/wp-json/wp/v2',
    'user' : 'Martin',
    'password' : 'n2sjKvQ9gVsiCPG2t8fcyAB0',
    'testfolder' : 'test'
}

wp_site3 = {
    'url' : 'http://127.0.0.1/wordpress',
    'rest_route' : '/wp-json/wp/v2',
    'user' : 'martin',
    'password' : 'uzDvXkWgOpz3eQlkArP39yzf',
    'testfolder' : 'test'
}

wp_site = wp_site2
wp_site['authentication'] = 'Basic ' + base64.b64encode( (wp_site['user'] + ':' + wp_site['password']).encode('ascii')).decode('ascii')
wp_big = 2560

# generate the WordPress-Class that will be tested
wp = WP_EXT_REST_API( wp_site )
print('Class generated')

# get all the image files from /testdata
testdata = os.path.join(SCRIPT_DIR, 'testdata')
files = os.listdir( testdata )
jpgfiles = [x for x in files if x.endswith('.jpg') == True]
webpfiles = [x for x in files if x.endswith('.webp') == True]
files = jpgfiles + webpfiles
newfiles = []
pythonmodules = dir()
pp = pprint.PrettyPrinter(indent=4, compact=True)

# prefix for the new created files
prefix = 'flip__'

cfpath = os.path.join(SCRIPT_DIR, 'createdfiles.json')
if os.path.isfile( cfpath ):
     f = open( cfpath )
     newfiles = json.load(f)
     f.close()
     os.remove(cfpath)

cfpath = os.path.join(SCRIPT_DIR, 'report.html')
if os.path.isfile( cfpath ):
     os.remove(cfpath)
     
print('Files collected')

# ------- pytest ficture to run before and after each test
@pytest.fixture(autouse=True)
def run_around_tests():
     """ Fixture to execute asserts before and after each test run. """
     # Setup: assertion before the test
     assert True
     #print('starting next test')
     
     yield # do the test

     # Teardown: assertion after the test
     assert True
     

# --------------- basic tests --------------------------------------------
@pytest.mark.basic
def test_info_about_test_site():
     print('--- Python sys.version: ', sys.version )
     print('--- imported python modules: ')
     pp.pprint( pythonmodules )
     print('--- SCRIPT_DIR: ', SCRIPT_DIR )
     print('--- SCRIPT_DIR2: ', SCRIPT_DIR2 )
     print('--- found image files in ../testdata/*.<types>: ', files )

@pytest.mark.basic
def test_rest_api_request_without_login():
     url = wp.url + wp.rest_route

     response = requests.get(url)
     print('--- Get URL ', url, ' with status code:', response.status_code )
     expected = 403
     if url.find('http:') >= 0:
          expected = 401
     assert response.status_code == expected # 403 for site with https:// and 401 for site with http://

@pytest.mark.basic
def test_rest_api_request_with_login_and_header():
     url = wp.url + wp.rest_route

     response = requests.get(url, headers=wp.headers )
     print('--- Get URL ', url, ' with status code:', response.status_code )
     assert response.status_code == 200

     # Validate response content type header
     assert response.headers["Content-Type"] == "application/json; charset=UTF-8"

@pytest.mark.basic
def test_rest_api_request_with_login_base_url():
     url = wp.url + '/wp-json/'

     response = requests.get(url, headers=wp.headers )
     resp_body = response.json()

     print('site-info:name : ', resp_body['name'])
     print('site-info:descr: ', resp_body['description'])

     assert resp_body['url'] == wp.url
     assert resp_body['home'] == wp.url

@pytest.mark.basic
def test_rest_api_request_https_status():
     url = wp.url + '/wp-json/wp-site-health/v1/tests/https-status'

     response = requests.get(url, headers=wp.headers )
     resp_body = response.json()

     expected = 'good'
     if url.find('http:') >= 0:
          expected = 'recommended'

     print('--- https-status: ', resp_body['status'])
     assert resp_body['status'] == expected # 'good' for site with https:// and 'recommended' for site with http://

@pytest.mark.basic
def test_wp_site_basic_tests():
     assert wp.isgutbgactive == True
     assert wp.tested_plugin_activated == True
     assert len(wp.active_plugins) > 0
     assert len(wp.plugins) > 0
     assert len(wp.active_theme) > 0

     print('--- tested Plugin Name: ', wp.tested_plugin_name )
     assert wp.tested_plugin_name == 'Ext_REST_Media_Lib'

     print('--- WP-Version: ', wp.wpversion )
     assert wp.wpversion == '5.8.0'

     print('--- wp.media_writeable_rest_fields: ',  wp.media_writeable_rest_fields )
     print('--- wp.mimetypes: ', wp.mimetypes ) 
     print('--- wp.wpversion: ',  wp.wpversion )
     print('--- wp.url: ', wp.url )
     print('--- wp.rest_route: ', wp.rest_route )
     print('--- wp.suburl: ', wp.suburl )
     print('--- wp.tested_plugin_dir: ', wp.tested_plugin_dir )
     print('--- wp.tested_plugin_name: ', wp.tested_plugin_name )
     print('--- wp.tested_plugin_min_version: ', wp.tested_plugin_min_version )
     print('--- files in createdfiles.json loaded to `newfiles`: ', newfiles )
     print(' !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
     print('IMPORTANT NOTE: COPY THE content of', wp.url + '/wp-admin/site-health.php?tab=debug into the clipboard and paste it in the *.html report to store all information about the test-site:')
     print('-----------------------------------------------------------------------------')
     # TODO: get the data from wp-site-health with chromium -> login -> call site-health -> click on 'copy to clipboard' -> catch the clipboard and paste + print it here at runtime.
     #       Quite an effort for an action that could be done manually in seconds. So this is postponed for the moment. Advantage is that the report will not contain sensitive information.
     # get the directory sizes
     print('--- Directory sizes: ')
     url = wp.url + '/wp-json/wp-site-health/v1/directory-sizes'
     response = requests.get(url, headers=wp.headers )
     resp_body = response.json()
     pp.pprint(resp_body)

@pytest.mark.basic
def test_rest_api_request_plugin_status():
     url = wp.url + '/wp-json/wp/v2/plugins'

     response = requests.get(url, headers=wp.headers )
     resp_body = response.json()

     print('--- PI-Name is:', wp.tested_plugin_name)
     print('--- PI-Version:', wp.tested_plugin_version )
     print('---------------------------------------------')
     print('--- Installed Plugins:')
     for pi in resp_body:
          print('------ ', pi['name'])
          print('             Version ', pi['version'], ' is ', pi['status'])
          #print('------------- Description:', pi['description']['rendered'] )
             
     assert ( StrictVersion( wp.tested_plugin_version ) >= wp.tested_plugin_min_version ) == True     

@pytest.mark.basic
def test_rest_api_request_active_theme():

     url = wp.url + '/wp-json/wp/v2/themes'

     response = requests.get(url, headers=wp.headers )
     resp_body = response.json()

     pi_index = find_plugin_in_json_resp_body(resp_body, 'status', 'active')

     print('--- Theme-Name is:', resp_body[pi_index]['stylesheet'] )
     print('---  Theme-Status:', resp_body[pi_index]['status'])
     print('--- Theme-Version:', resp_body[pi_index]['version'] )
     print('---------------------------------------------')
     print('--- Installed Themes:')
     for pi in resp_body:
          print('------ ', pi['name']['rendered'])
          print('             Version ', pi['version'], ' is ', pi['status'])
          #print('------------- ', pi['version'] )
          #print('------------- Description:', pi['description']['rendered'] )

     assert pi_index >= 0
     assert resp_body[pi_index]['status'] == 'active'
     assert ( StrictVersion( resp_body[pi_index]['version'] ) >= '0.0.1' ) == True

# TODO: upload one image to the standard folder. It is requiredd for the 
# following tests to have at least on image in the WP media-library. Could be necessary if the site was installed completely new for the test.

# --------------- extbasic tests: ext rest api --------------------------------
@pytest.mark.extbasic
def test_rest_api_get_field_gallery_with_invalid_id():
     # Now compare the new data
     result = wp.get_rest_fields( 99999999999999, 'media' )
     assert result['httpstatus'] == 404

@pytest.mark.extbasic
def test_rest_api_set_field_gallery_with_invalid_id():
     # Now compare the new data
     rest_fields = { 
               'gallery' : 'wrong_gallery'
               }
     result = wp.set_rest_fields( 999999999999999, 'media', rest_fields ) 
     assert result['httpstatus'] == 404

@pytest.mark.extbasic
def test_rest_api_set_field_gallery_sort_with_invalid_id():
     # Now compare the new data
     rest_fields = { 
               'gallery_sort' : '999999'
               }
     result = wp.set_rest_fields( 999999999999999, 'media', rest_fields ) 
     assert result['httpstatus'] == 404

@pytest.mark.extbasic
def test_rest_api_get_update_meta_with_invalid_id():
     # Now compare the new data
     result = wp.get_attachment_image_meta( 99999999999999 )
     assert result['httpstatus'] == 404

@pytest.mark.extbasic
def test_rest_api_set_update_meta_with_invalid_id(): 
     sid = '11'
     ts = '00'
     # set now the image_meta. Done here to have the same timestamp ts
     fields =  {'image_meta' : {
          "aperture": sid,
          "credit": 'Martin' + '_' + ts,
          "camera": "camera" + '_' + ts,
          "caption": 'caption' + sid + '_' + ts,
          "created_timestamp": ts,
          "copyright": "copy" + '_' + ts,
          "focal_length": sid,
          "iso": sid,
          "shutter_speed": "0." + sid,
          "title": 'title' + sid + '_' + ts,
          "orientation": "1",
          "keywords": [ 'generated' + '_' + ts]
     } }

     result = wp.set_attachment_image_meta( 99999999999, 'media', fields )
     assert result['httpstatus'] == 404

@pytest.mark.extbasic
def test_rest_api_addtofolder_with_invalid_folder():
     folder = 'folder_that_does_not_exist'
     result=wp.get_add_image_to_folder( folder )
     msg = result['message']
     s1 = 'You requested image addition to folder '
     s2 = '/uploads/' + folder + ' with GET-Request. Please use POST Request.'
     match = re.search(s1 + "[a-zA-Z0-9-_/.:]+" +s2, msg)
     assert result['httpstatus'] == 200
     assert result['exists'] == 'Could not find directory'
     assert match != None

@pytest.mark.extbasic
def test_rest_api_addtofolder_with_valid_folder():
     folder = wp.tested_site['testfolder']
     result=wp.get_add_image_to_folder( folder )
     msg = result['message']
     s1 = 'You requested image addition to folder ' #'You requested image addition to folder '
     s2 = '/uploads/' + folder + ' with GET-Request. Please use POST Request.' # '/uploads/folder_that_does_not_exist with GET-Request. Please use POST Request.'
     match = re.search(s1 + "[a-zA-Z0-9-_/.:]+" +s2, msg) # 'You requested image addition to folder C:/Bitnami/wordpress-5.2.2-0/apps/wordpress/htdocs/wp-content/uploads/folder_that_does_not_exist with GET-Request. Please use POST Request.'
     assert result['httpstatus'] == 200
     assert result['exists'] == 'OK'
     assert match != None

@pytest.mark.extbasic
def test_rest_api_addtofolder_with_standard_folder():
     folder = datetime.datetime.now(datetime.timezone.utc).strftime("%Y/%m")
     files = os.listdir( testdata )
     jpgfiles = [x for x in files if x.endswith('.jpg') == True]
     webpfiles = [x for x in files if x.endswith('.webp') == True]
     newfiles = jpgfiles + webpfiles

     result=wp.post_add_image_to_folder( folder, newfiles[0])
     msg = result['message']
        
     assert result['httpstatus'] == 400, 'Will fail if the upload was not possible.'
     assert msg == "Do not add image to WP standard media directory"

@pytest.mark.extbasic
def test_rest_api_addtofolder_with_valid_folder_file_exists():
     folder = wp.tested_site['testfolder']
     files = os.listdir( testdata )
     jpgfiles = [x for x in files if x.endswith('.jpg') == True]
     webpfiles = [x for x in files if x.endswith('.webp') == True]
     newfiles = jpgfiles + webpfiles

     result= wp.post_add_image_to_folder( folder, newfiles[0])
     id = result['id']

     result=wp.post_add_image_to_folder( folder, newfiles[0])
     
     wp.delete_media( id , 'media' )
          
     assert result['httpstatus'] == 400, "The assertion will fail if the file didn't exist before. Http-status is then 200 because the file was successfully uploaded."
     assert result['code'] == 'error'

@pytest.mark.extbasic
def test_rest_api_addtofolder_with_valid_folder_file_exists_wrong_mimetype():
     folder = wp.tested_site['testfolder']
     files = os.listdir( testdata )
     jpgfiles = [x for x in files if x.endswith('.jpg') == True]
     webpfiles = [x for x in files if x.endswith('.webp') == True]
     newfiles = jpgfiles + webpfiles

     fname = newfiles[0]
     # read the image file to a binary string
     path = os.getcwd()
     fname = os.path.join(path, 'testdata', fname)
     fin = open(fname, "rb")
     data = fin.read()
     fin.close()

     #get the base filename with extension
     imagefile = os.path.basename( fname )

     # check image mime
     mime = magic.Magic(mime=True)
     mimetype = mime.from_file(fname)
     if mimetype == 'image/jpeg':
          mimetype = 'image/webp'
     else:
          mimetype = 'image/jpeg'
     
     # upload new image
     geturl = wp.url + '/wp-json/extmedialib/v1/addtofolder/' + folder
     # set the header. 
     header = wp.headers
     header['Content-Disposition'] = 'attachment; filename=' + imagefile
     header['Content-Type'] = mimetype

     resp_body = {}
     response = requests.post(geturl, headers=header, data=data )
     resp_body.update( json.loads( response.text) )
     result = resp_body
    
     assert result['data']['status'] == 400, 'Will fail if the upload was not possible.'
     assert result['code'] == 'error'


# --------------- image tests with ext rest api --------------------------------
@pytest.mark.updateimage ###########
@pytest.mark.testimage
def test_get_number_of_posts_and_upload_dir():
     wp.get_number_of_posts() 
     print ('--- Counted ' +  str(wp.media['count']) + ' images in the media library.')
     assert wp.media['count'] > 0
     wp.real_wp_upload_dir = wp.wp_upload_dir
     wp.wp_upload_dir = wp.wp_upload_dir + wp.tested_site['testfolder'] + '/'
     
@pytest.mark.testimage #################
@pytest.mark.parametrize( "image_file", files)
def test_image_upload_to_folder_with_ext_rest_api( image_file ):
     createdfiles = []
     image_number_before = wp.media['count']

     # get current time and
     # assume a maximumt offset of 5 secondes between server and local machine that runs the test
     uploadtime = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
     uploadtime = datetime.datetime.strptime( uploadtime, "%Y-%m-%dT%H:%M:%S") - datetime.timedelta(seconds=5) 

     print('--- Uploading file: ', image_file)
     result=wp.post_add_image_to_folder( wp.tested_site['testfolder'], image_file)

     print('--- ', result['message'])
     # check the upload status. 
     assert result['httpstatus'] == 200
     
     if result['httpstatus'] == 200:
          current = len(wp.created_images)
          if current == 0: 
               n = 0
          else:  
               n = current

          wp.created_images[n] = {}
          wp.created_images[n]['id'] = result['id']
          wp.created_images[n]['gallery'] = result['gallery']
          wp.created_images[n]['original_file'] = result['new_file_name']
          wp.last_media_id = result['id']
          wp.last_index_in_created_images = n

          #save filename and id
          if (n+1) == len(files):
               for i in range(0, n+1):
                    createdfiles.append( [ wp.created_images[i]['id'], wp.created_images[i]['original_file']  ] )
               with open('createdfiles.json', 'w', encoding='utf-8') as f:
                    json.dump( createdfiles, f, ensure_ascii=False, indent=4)

     # check the media id of the new created image in the media library
     print('--- last media id: ', wp.media['maxid'])
     print('--- new media id: ', result['id'])
     assert result['id'] > wp.media['maxid']
     if result['id'] > wp.media['maxid']:
          wp.media['maxid'] = result['id']

     # check the gallery
     print('--- gallery: ', result['gallery'])
     assert result['gallery'] == wp.tested_site['testfolder']

     # check the number of media in the media library
     wp.get_number_of_posts()
     wp.real_wp_upload_dir = wp.wp_upload_dir
     wp.wp_upload_dir = wp.wp_upload_dir + wp.tested_site['testfolder'] + '/'
     print('--- new image count: ', wp.media['count'])
     assert wp.media['count'] == image_number_before + 1

     # retrieve the rest-response for the new created image
     result = wp.get_post_content( wp.media['maxid'], 'media' )
     # store the rest response to /media/id to wp.created_images
     if result['httpstatus'] == 200:
          wp.created_images[n]['post'] =  result
     
     # check wordpress site uses complete url. check with the uploaded image, because older images could be different.
     print('--- guid for decision: ', result['guid']['rendered'])
     print('--- wp.baseurl for decision: ', wp.baseurl)
     pos = result['guid']['rendered'].find( wp.baseurl )
     if pos>-1:
          wp.usescompleteurls = True
          print('--- Site uses complete urls!')
     else:
          wp.usescompleteurls = False
          print('--- Site does not use complete urls!')
     
     # create the dictionaries required for checking
     # requires that test_get_number_of_posts_and_upload_dir or wp.get_number_of_posts() was executed before to be correct!
     path = os.path.join(SCRIPT_DIR, 'testdata', image_file)
     assert os.path.isfile( path ) == True
     im = Image.open( path )
     (width, height) = im.size
     im.close()

     if width > wp_big or height > wp_big:
          wp.img_isscaled = True
          print('--- image is scaled: Yes')

     wp.generate_dictfb(image_file)
     wp.generate_dictall()

     # check the attachment type
     print('--- attachment type: ', result['media_type'])
     assert result['media_type'] == 'image'

     # check the guid
     print('--- guid: ', result['guid']['rendered'])
     assert result['guid']['rendered'] == wp.dictall['guid']
    
     # check the source url
     print('--- source-url: ', result['source_url'])
     assert result['source_url'] == wp.dictall['sourceUrl']
     
     # check the link url
     print('--- link: ', result['link'])
     assert result['link'] == wp.dictall['link'], 'Don\'t worry. This might fail if an image with the same name already exists in the WP media library.'

     # check the time
     imagetime = datetime.datetime.strptime( result['modified_gmt'], "%Y-%m-%dT%H:%M:%S")
     print('--- time: ', uploadtime, 'image-time: ', result['modified_gmt'])
     assert imagetime >= uploadtime # format "2021-08-16T14:51:39" upload-time
     
     # check image mime
     mime = magic.Magic(mime=True)
     mimetype = mime.from_file( path )
     print('--- mime-type: ', result['mime_type'])
     assert result['mime_type'] == mimetype # "image/jpeg" oder "image/webp"

     # do all the rest
     assert result['slug'] == wp.dictall['slug'] 
     assert result['title']['rendered'] == wp.dictall['title'] 
     assert result['source_url'] == wp.dictall['sourceUrl'] 
     
     pos = wp.baseurl.find('127.0.0.1')
     if pos == -1:
          assert result['media_details']['file'] == wp.dictall['mediaDetailsFile'] # This one can't be checked for my local site because it uses the local path
          # for the remote site this check is OK
     if wp.img_isscaled:
          assert result['media_details']['original_image'] == wp.dictall['mediaDetailsoriginalFile'] 

     # check the media-details   
     for size in result['media_details']['sizes']:
          m = len(re.findall( wp.dictall['mediaDetailsSizesFile'], result['media_details']['sizes'][size]['file']))
          if size == 'full': assert m == 0 
          else: assert m == 1
          m = len(re.findall( wp.dictall['mediaDetailsSizesSrcUrl'], result['media_details']['sizes'][size]['source_url']))
          if size == 'full': assert m == 0 
          else: assert m == 1

# Mind: the generated IDs are not known before the test, but the filenames are.
# So, the generated IDs are loaded from an intermediate file to list 'newfiles', that should be deleted afterwards
# or at least right before the next test
@pytest.mark.updateimage ##############
@pytest.mark.testimage
def test_created_json_file_list():
     global newfiles

     cfpath = os.path.join(SCRIPT_DIR, 'createdfiles.json')
     print('--- Read created files from: ', cfpath)
     assert os.path.isfile( cfpath ) == True

     if os.path.isfile( cfpath ):
          f = open( cfpath )
          newfiles = json.load(f)
          f.close()

@pytest.mark.testfield # -----------------
@pytest.mark.parametrize( "image_file", files)
def test_ext_rest_api_get_md5_sum( image_file ):
     image_file = get_image( newfiles, image_file) 

     if type(image_file) == list:
          cfpath = os.path.join(SCRIPT_DIR, 'testdata', image_file[1])
          print('--- Calc MD5 from: ', cfpath)
          assert os.path.isfile( cfpath ) == True

          if os.path.isfile( cfpath ):
               id = image_file[0]
               md5sum = hashlib.md5(open( cfpath,'rb').read()).hexdigest()
               md5sum = md5sum.upper()
               print('--- MD5 of local file: ', md5sum)
          
               # Now compare the new data
               result = wp.get_rest_fields( id, 'media' )
               assert result['httpstatus'] == 200 

               if result['httpstatus'] == 200:
                    assert result["md5_original_file"]['MD5'] == md5sum

@pytest.mark.testfield # -----------------
@pytest.mark.parametrize( "image_file", files)
def test_rest_api_set_field_gallery_with_valid_id_new_value( image_file ):
     image_file = get_image( newfiles, image_file) 

     if type(image_file) == list:
          id = image_file[0]
          result = wp.get_rest_fields( id, 'media' )
          old = result['gallery']
          new = old[::-1]
          # Now compare the new data
          rest_fields = { 
                    'gallery' : new
                    }
          result = wp.set_rest_fields( id, 'media', rest_fields ) 
          assert result['httpstatus'] == 200
          # recover the previous value
          rest_fields = { 
                    'gallery' : old
                    }
          result = wp.set_rest_fields( id, 'media', rest_fields )

@pytest.mark.testfield # -----------------
@pytest.mark.parametrize( "image_file", files)
def test_rest_api_set_field_gallery_with_valid_id_same_value( image_file ):
     image_file = get_image( newfiles, image_file) 

     if type(image_file) == list:
          id = image_file[0]
          result = wp.get_rest_fields( id, 'media' )
          old = result['gallery']
          # Now compare the new data
          rest_fields = { 
                    'gallery' : old
                    }
          result = wp.set_rest_fields( id, 'media', rest_fields ) 
          assert result['httpstatus'] == 200

@pytest.mark.testfield # -----------------
@pytest.mark.parametrize( "image_file", files)
def test_rest_api_set_field_gallery_sort_with_valid_id_new_value( image_file ):
     image_file = get_image( newfiles, image_file) 

     if type(image_file) == list:
          id = image_file[0]
          #result = wp.get_rest_fields( id, 'media' )
          #old = int(result['gallery_sort'])
          new = id+1
          # Now compare the new data
          rest_fields = { 
                    'gallery_sort' : str(id)
                    }
          result = wp.set_rest_fields( id, 'media', rest_fields ) 
          assert result['httpstatus'] == 200

@pytest.mark.testfield # -----------------
@pytest.mark.parametrize( "image_file", files)
def test_rest_api_set_field_gallery_sort_with_valid_id_same_value( image_file ):
     image_file = get_image( newfiles, image_file) 

     if type(image_file) == list:
          id = image_file[0]
          result = wp.get_rest_fields( id, 'media' )
          old = result['gallery_sort']
          # Now compare the new data
          rest_fields = { 
                    'gallery_sort' : old
                    }
          result = wp.set_rest_fields( id, 'media', rest_fields ) 
          assert result['httpstatus'] == 200

@pytest.mark.testimage ############
@pytest.mark.parametrize( "image_file", files)
def test_rest_api_get_update_meta_with_valid_id( image_file ):
     image_file = get_image( newfiles, image_file) 

     if type(image_file) == list:
          id = image_file[0]
          result = wp.get_attachment_image_meta( id ) 
          assert result['httpstatus'] == 405

@pytest.mark.testimage ############
@pytest.mark.parametrize( "image_file", files)     
def test_id_of_created_images( image_file ):
     image_file = get_image( newfiles, image_file)

     if type(image_file) == list:
          id = image_file[0]
          file = image_file[1]
          print('entry: ', image_file, ' is type ', type(image_file), '. ID=',id, 'and file is', file)
          assert isinstance(id, int) == True
          assert isinstance(file, str) == True
     else:     
          #img = wp.created_images[ wp.last_index_in_created_images ]
          id = wp.last_media_id
          assert isinstance(id, int) == True

          end = len(wp.created_images)
          for i in range(0, end): 
               assert isinstance( wp.created_images[i]['id'], int) == True 
      
@pytest.mark.testimage ############
@pytest.mark.parametrize( "image_file", files)
def test_update_image_metadata( image_file ): 
     image_file = get_image( newfiles, image_file)
     uploadtime = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
     uploadtime = datetime.datetime.strptime( uploadtime, "%Y-%m-%dT%H:%M:%S") - datetime.timedelta(seconds=10) 

     if type(image_file) == list:
          id = image_file[0]
          sid = str(id)
          imgfile = image_file[1]
          ts = str( round(datetime.datetime.now().timestamp()) )
          rest_fields = { 
               'title' :        'title' + sid + '_' + ts, 
               'gallery_sort' : sid, 
               'description' : 'descr' + sid + '_' + ts, 
               'caption' :     'caption' + sid + '_' + ts, 
               'alt_text' :    'alt_text' + sid + '_' + ts,
               'docaption' : 'true' 
               }

          result = wp.set_rest_fields( id, 'media', rest_fields )
          assert result['httpstatus'] == 200 

          # set now the image_meta. Done here to have the same timestamp ts
          fields =  {'image_meta' : {
            "aperture": sid,
            "credit": 'Martin' + '_' + ts,
            "camera": "camera" + '_' + ts,
            "caption": 'caption' + sid + '_' + ts,
            "created_timestamp": ts,
            "copyright": "copy" + '_' + ts,
            "focal_length": sid,
            "iso": sid,
            "shutter_speed": "0." + sid,
            "title": 'title' + sid + '_' + ts,
            "orientation": "1",
            "keywords": [ 'generated' + '_' + ts]
          } }

          result = wp.set_attachment_image_meta( id, 'media', fields )
          assert result['httpstatus'] == 200

          # Now compare the new data
          result = wp.get_rest_fields( id, 'media' )
          assert result['httpstatus'] == 200 

          print ('Comparing: ', result['id'])  
          assert result['id'] == id

          print('--- title: ', result['title']['rendered'] )
          assert result['title']['rendered'] == rest_fields['title']

          print('--- gallery_sort: ', result['gallery_sort'] )
          assert result['gallery_sort'] == rest_fields['gallery_sort']

          # result['description'] == rest_fields['description'] # can't check the description, as this contains the srcset, too
          cap = remove_html_tags( result['caption']['rendered'] )
          print('--- caption: ', cap )
          assert cap == rest_fields['caption']

          print('--- alt_text: ', rest_fields['alt_text'] )
          assert result['alt_text'] == rest_fields['alt_text']

          # check the attachment type
          print('--- attachment type: ', result['media_type'])
          assert result['media_type'] == 'image'

          # check the gallery
          print('--- gallery: ', result['gallery'])
          assert result['gallery'] == wp.tested_site['testfolder']

          # check the guid
          print('--- guid: ', result['guid']['rendered'])
          assert result['guid']['rendered'] == wp.dictall['guid']
         
          # check the link url
          print('--- link: ', result['link'])
          assert result['link'] == wp.dictall['link'], 'Don\'t worry. This might fail if an image with the same name already exists in the WP media library.'
         
          # check the time
          imagetime = datetime.datetime.strptime( result['modified_gmt'], "%Y-%m-%dT%H:%M:%S")
          print('--- time: ', uploadtime, 'image-time: ', result['modified_gmt'])
          assert imagetime >= uploadtime # format "2021-08-16T14:51:39" upload-time

          # check image mime
          path = os.getcwd()
          fullpath = os.path.join(path, 'testdata', imgfile)
          mime = magic.Magic(mime=True)
          mimetype = mime.from_file( fullpath )
          print('--- mime-type: ', result['mime_type'])
          assert result['mime_type'] == mimetype # "image/jpeg" oder "image/webp"

          # check the image_meta: complete for webg
          if mimetype == 'image/webp':
               assert result['media_details']['image_meta'] == fields['image_meta']
          # for jpg only Common items: 'caption', 'copyright', 'credit', 'keywords', 'title'
          if mimetype == 'image/jepg':
               assert result['media_details']['image_meta']['caption'] == fields['image_meta']['caption']
               assert result['media_details']['image_meta']['copyright'] == fields['image_meta']['copyright']
               assert result['media_details']['image_meta']['credit'] == fields['image_meta']['credit']
               assert result['media_details']['image_meta']['title'] == fields['image_meta']['title']
               assert result['media_details']['image_meta']['keywords'] == fields['image_meta']['keywords']

@pytest.mark.testpost # --------------
@pytest.mark.parametrize( "image_file", files)
def test_create_gtb_image_with_one_image( image_file ): 
     image_file = get_image( newfiles, image_file)
     ts = str( round(datetime.datetime.now().timestamp()) )

     if type(image_file) == list:
          id = image_file[0]
          content = wp.create_wp_image_gtb(id)
          data = \
          {
               "title":"Post with one Image " + ts,
               "content": content,
               "status": "publish",
          }

          result = wp.add_post( data, 'post' )
          assert result['httpstatus'] == 201

          if result['httpstatus'] == 201:
               current = len(wp.created_posts)
               if current == 0: 
                    n = 0
               else:  
                    n = current
               wp.created_posts[n] = {}
               wp.created_posts[n]['id'] = result['id']
               wp.created_posts[n]['used_image'] = id
               wp.created_posts[n]['type'] = 'wp-image'

               # retrieve the rest-response for the new created post
               result = wp.get_post_content( result['id'], 'posts' )
               # store the rest response to /media/id to wp.created_images
               if result['httpstatus'] == 200:
                    wp.created_posts[n]['post'] =  result

@pytest.mark.testpost # --------------
def test_create_gtb_gallery_with_all_images():
     ts = str( round(datetime.datetime.now().timestamp()) )
     allimgs = newfiles
     ids = {}
     ind = 0
     for i in allimgs:
          ids[ind] = str(i[0])
          ind = ind +1

     content = wp.create_wp_gallery_gtb( ids, 3, 'Erste Galerie!')

     data = \
          {
               "title":"Galerie with all images " + ts,
               "content": content,
               "status": "publish",
          }

     result = wp.add_post( data, 'post' )
     assert result['httpstatus'] == 201

     if result['httpstatus'] == 201:
          current = len(wp.created_posts)
          if current == 0: 
               n = 0
          else:  
               n = current
          wp.created_posts[n] = {}
          wp.created_posts[n]['id'] = result['id']
          wp.created_posts[n]['used_image'] = ids
          wp.created_posts[n]['type'] = 'wp-gallery'

          # retrieve the rest-response for the new created post
          result = wp.get_post_content( result['id'], 'posts' )
          # store the rest response to /media/id to wp.created_images
          if result['httpstatus'] == 200:
               wp.created_posts[n]['post'] =  result

@pytest.mark.testpost # --------------
@pytest.mark.parametrize( "image_file", files)
def test_create_gtb_image_text( image_file ): 
     image_file = get_image( newfiles, image_file)
     ts = str( round(datetime.datetime.now().timestamp()) )

     if type(image_file) == list:
          id = image_file[0]
          content = wp.create_wp_media_text_gtb(id, 'Created at: ' + ts)
          data = \
          {
               "title":"Post with one Image and Text " + ts,
               "content": content,
               "status": "publish",
          }

          result = wp.add_post( data, 'post' )
          assert result['httpstatus'] == 201

          if result['httpstatus'] == 201:
               current = len(wp.created_posts)
               if current == 0: 
                    n = 0
               else:  
                    n = current
               wp.created_posts[n] = {}
               wp.created_posts[n]['id'] = result['id']
               wp.created_posts[n]['used_image'] = id
               wp.created_posts[n]['type'] = 'wp-image-text'

               # retrieve the rest-response for the new created post
               result = wp.get_post_content( result['id'], 'posts' )
               # store the rest response to /media/id to wp.created_images
               if result['httpstatus'] == 200:
                    wp.created_posts[n]['post'] =  result

@pytest.mark.testimage #############
@pytest.mark.parametrize( "image_file", files)
def test_update_image_metadata_after_posts_were_created( image_file ): 
     image_file = get_image( newfiles, image_file)
     uploadtime = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
     uploadtime = datetime.datetime.strptime( uploadtime, "%Y-%m-%dT%H:%M:%S") - datetime.timedelta(seconds=10) 
     pre = 'updated_'

     if type(image_file) == list:
          id = image_file[0]
          sid = str(id)
          imgfile = image_file[1]
          ts = str( round(datetime.datetime.now().timestamp()) )
          rest_fields = { 
               'title' :        pre + 'title' + sid + '_' + ts, 
               'gallery_sort' : sid, 
               'description' : pre + 'descr' + sid + '_' + ts, 
               'caption' :     pre + 'caption' + sid + '_' + ts, 
               'alt_text' :    pre + 'alt' + sid + '_' + ts,
               'docaption': 'true' 
               }

          result = wp.set_rest_fields( id, 'media', rest_fields )
          print('--- timestamp: ', ts)
          assert result['httpstatus'] == 200 

          # set now the image_meta. Done here to have the same timestamp ts
          fields =  {'image_meta' : {
            "aperture": sid,
            "credit": 'Martin' + '_' + ts,
            "camera": "camera" + '_' + ts,
            "caption": pre + 'caption' + sid + '_' + ts,
            "created_timestamp": ts,
            "copyright": "copy" + '_' + ts,
            "focal_length": sid,
            "iso": sid,
            "shutter_speed": "0." + sid,
            "title": pre + 'title' + sid + '_' + ts,
            "orientation": "1",
            "keywords": [ pre + 'generated' + '_' + ts]
            #'alt_text' :    pre + 'alt' + sid + '_' + ts 
          } }

          result = wp.set_attachment_image_meta( id, 'media', fields )
          assert result['httpstatus'] == 200
          
          # wait a second for the wp database
          time.sleep(1)
          # Now compare the new data
          result = wp.get_rest_fields( id, 'media' )
          assert result['httpstatus'] == 200 

          print ('Comparing: ', result['id'])  
          assert result['id'] == id

          print('--- title: ', result['title']['rendered'] )
          assert result['title']['rendered'] == rest_fields['title']

          print('--- gallery_sort: ', result['gallery_sort'] )
          assert result['gallery_sort'] == rest_fields['gallery_sort']

          # result['description'] == rest_fields['description'] # can't check the description, as this contains the srcset, too
          cap = remove_html_tags( result['caption']['rendered'] )

          print('--- caption: ', cap )
          assert cap == rest_fields['caption']

          if 'alt_text' in rest_fields:
               print('--- alt_text: ', rest_fields['alt_text'] )
               assert result['alt_text'] == rest_fields['alt_text']

          # check the attachment type
          print('--- attachment type: ', result['media_type'])
          assert result['media_type'] == 'image'

          # check the gallery
          print('--- gallery: ', result['gallery'])
          assert result['gallery'] == wp.tested_site['testfolder']

          # check the guid
          print('--- guid: ', result['guid']['rendered'])
          assert result['guid']['rendered'] == wp.dictall['guid']
         
          # check the link url
          print('--- link: ', result['link'])
          assert result['link'] == wp.dictall['link'], 'Don\'t worry. This might fail if an image with the same name already exists in the WP media library.'

          # check the time
          imagetime = datetime.datetime.strptime( result['modified_gmt'], "%Y-%m-%dT%H:%M:%S")
          print('--- time: ', uploadtime, 'image-time: ', result['modified_gmt'])
          assert imagetime >= uploadtime # format "2021-08-16T14:51:39" upload-time

          # check image mime
          path = os.getcwd()
          fullpath = os.path.join(path, 'testdata', imgfile)
          mime = magic.Magic(mime=True)
          mimetype = mime.from_file( fullpath )
          print('--- mime-type: ', result['mime_type'])
          assert result['mime_type'] == mimetype # "image/jpeg" oder "image/webp"

          # check the image_meta: complete for webg
          if mimetype == 'image/webp':
               assert result['media_details']['image_meta'] == fields['image_meta']
          # for jpg only Common items: 'caption', 'copyright', 'credit', 'keywords', 'title'
          if mimetype == 'image/jepg':
               assert result['media_details']['image_meta']['caption'] == fields['image_meta']['caption']
               assert result['media_details']['image_meta']['copyright'] == fields['image_meta']['copyright']
               assert result['media_details']['image_meta']['credit'] == fields['image_meta']['credit']
               assert result['media_details']['image_meta']['title'] == fields['image_meta']['title']
               assert result['media_details']['image_meta']['keywords'] == fields['image_meta']['keywords']

@pytest.mark.testimage #############
@pytest.mark.parametrize( "image_file", files)
def test_update_image_with_flipped_original_and_new_filename( image_file ): 
     # this if-else is here for debugging
     #if __name__ == '__main__':
     #     image_file = [1950, 'Schlossinsel-Mirow-13_klein.webp']
     #else:
     image_file = get_image( newfiles, image_file)
   
     if type(image_file) == list:
          id = image_file[0]
          imgfile = image_file[1]
          ts = str( round(datetime.datetime.now().timestamp()) )

          path = os.path.join(SCRIPT_DIR, 'testdata', imgfile)
          assert os.path.isfile( path ) == True

          # Flip the image and save it with new name 'flipped_<old-name>'
          im = Image.open( path )
          im = ImageOps.flip( im )
          newimg = prefix + imgfile
          path = os.path.join(SCRIPT_DIR, 'createddata', newimg)
          im.save( path )

          # update the new url and link dicts
          # create the dictionaries required for checking
          # requires that test_get_number_of_posts_and_upload_dir or wp.get_number_of_posts() was executed before to be correct!
          im = Image.open( path )
          (width, height) = im.size
          im.close()

          if width > wp_big or height > wp_big:
               wp.img_isscaled = True
               print('--- image is scaled: Yes')

          wp.generate_dictfb( newimg )
          wp.generate_dictall()

          # upload the flipped image with the new name but the same id
          # keep the mime-type as is (for the moment)
          result = wp.post_update_image( id, path, False )
          print('--- local path updated file: ', path)
          assert result['httpstatus'] == 200
                   
          # Now compare the new data
          result = wp.get_rest_fields( id, 'media' )
          assert result['httpstatus'] == 200 

          print ('Comparing: ', result['id'])  
          assert result['id'] == id

          # check the gallery
          print('--- gallery: ', result['gallery'])
          assert result['gallery'] == wp.tested_site['testfolder']

          # check the attachment type
          print('--- attachment type: ', result['media_type'])
          assert result['media_type'] == 'image'

          # check the guid
          print('--- guid: ', result['guid']['rendered'])
          assert result['guid']['rendered'] == wp.dictall['guid']
     
          # check the source url
          print('--- source-url: ', result['source_url'])
          assert result['source_url'] == wp.dictall['sourceUrl']
          
          # check the link url
          print('--- link: ', result['link'])
          assert result['link'] == wp.dictall['link'], 'Don\'t worry. This might fail if an image with the same name already exists in the WP media library.'

          # check image mime
          mime = magic.Magic(mime=True)
          mimetype = mime.from_file( path )
          print('--- mime-type: ', result['mime_type'])
          assert result['mime_type'] == mimetype # "image/jpeg" oder "image/webp"

          # do all the rest
          assert result['slug'] == wp.dictall['slug'] 
          assert result['title']['rendered'] == wp.dictall['title'] 
          assert result['source_url'] == wp.dictall['sourceUrl'] 

          # special cases for my localhost on windows
          pos = wp.baseurl.find('127.0.0.1')
          if pos == -1:
               assert result['media_details']['file'] == wp.dictall['mediaDetailsFile'] # This one can't be checked for my local site because it uses the local path
               # for the remote site this check is OK
          if wp.img_isscaled:
               assert result['media_details']['original_image'] == wp.dictall['mediaDetailsoriginalFile'] 

          # check the media-details and the description.rendered  
          descr = result['description']['rendered']
          for size in result['media_details']['sizes']:
               m = len(re.findall( wp.dictall['mediaDetailsSizesFile'], result['media_details']['sizes'][size]['file']))
               if size == 'full': assert m == 0 
               else: assert m == 1
               m = len(re.findall( wp.dictall['mediaDetailsSizesSrcUrl'], result['media_details']['sizes'][size]['source_url']))
               if size == 'full': assert m == 0 
               else: assert m == 1
               m = len(re.findall( wp.dictall['mediaDetailsSizesSrcUrl'], descr))
               if size == 'full': assert m == 0 
               else: assert m == 1, 'This might fail if there are special subsizes used that are not used for the srcset.'
    

@pytest.mark.testpost
@pytest.mark.parametrize( "image_file", files)
def xtest_updated_posts_with_images( image_file ):
     image_file = get_image( newfiles, image_file)
     end = len(wp.created_posts)

     if type(image_file) == list:
          id = image_file[0]
          img = image_file[1]

          # loop through all created posts 
          for i in range(0, end):
               post = wp.created_posts[i]

               if id == post['used_image'] and not post['type'] == 'wp-gallery':
                    print('--- Found image ', id, ' in post ', post['id'], '. Now comparing with content.')
                    postid = post['id']
                    isimage = post['type'] == 'wp-image'

                    # get the image data
                    result = wp.get_post_content( id, 'media' )
                    assert result['httpstatus'] == 200
                    imgcaption = remove_html_tags( result['caption']['rendered'] )
                    imgalt = result['alt_text']
               
                    # get the post data
                    result = wp.get_post_content( postid, 'posts' )
                    assert result['httpstatus'] == 200
                    content = result['content']['rendered']       
                         
                    # compare now alt and caption. These two have to be changed in a gtb wp:image
                    found = content.find( 'alt="' + imgalt )
                    print(content)
                    print('--- imgalt: ', imgalt)
                    assert found > 10

                    if isimage:
                         found = content.find( '>' + imgcaption + '</' )
                         print('--- ', imgcaption)
                         assert found > 10

                    #compare the img src="...."
                    basename = os.path.splitext( img )[0]
                    ext = os.path.splitext( img )[1]
                    s1 = 'src="' + wp.suburl + wp.wp_upload_dir + prefix + basename # s1 = src="/wp-content/uploads/pythontest2/DSC_1722 
                    if  wp.usescompleteurls:
                         s1 = 'src="' + wp.wp_upload_url + wp_site['testfolder'] + '/' + prefix + basename
                    s2 = ext
                    match = len(re.findall( s1 + "-[0-9]+x[0-9]+" + s2, content)) # content src="/wordpress/wp-content/uploads/pythontest2/flippedDSC_1722.webp"
                    if match == 0:
                         match = len(re.findall( s1 + s2, content))
                    print('--- img src 1st part: ', s1)
                    assert match == 1

                    # compare the data-link
                    # bug TODO: the data-link in the wp:galery is not being updated! 
                    # bug TODO: the mediaLink in the wp:image and wp:media-text : same problem, is result['link'] also
                    # explink = result['link']
                    # match = len(re.findall( explink, content) ) 
                    # print('--- data-link:', explink)
                    #assert match == 1
                    
@pytest.mark.testpost
def xtest_updated_post_with_gallery():
     end = len(wp.created_posts)

     for i in range(0, end):
          if wp.created_posts[i]['type'] == 'wp-gallery':
               postid = wp.created_posts[i]['id']
               print('--- Found gallery ', postid, ' Now comparing with content.')

     # get the post data
     result = wp.get_post_content( postid, 'posts' )
     assert result['httpstatus'] == 200
     content = result['content']['rendered']

     allimgs = newfiles
     for i in allimgs:
          id = str(i[0]) # this is the image id
          img = i[1]

          # get the image data
          result = wp.get_post_content( id, 'media' )
          assert result['httpstatus'] == 200
          imgcaption = remove_html_tags( result['caption']['rendered'] )
          imgalt = result['alt_text']

          # compare now alt and caption. These two have to be changed in a gtb wp:image
          found = content.find( 'alt="' + imgalt )
          print(content)
          print('--- ', imgalt)
          assert found > 10

          found = content.find( '>' + imgcaption + '</' )
          print('--- ', imgcaption)
          assert found > 10

          #compare the data-full-url
          explink = 'data-full-url="' + wp.suburl + wp.real_wp_upload_dir + result['media_details']['file']
          if wp.usescompleteurls:
               explink = 'data-full-url="' + wp.wp_upload_url + result['media_details']['file']
          match = len(re.findall( explink, content) ) # content : data-full-url="/wordpress/wp-content/uploads/pythontest2/flippedDSC_1722.webp"
          print('--- data-full-url:', explink) #                  data-full-url="                              pythontest2/flippedDSC_1722.webp
          assert match == 1

          #compare the img src="...."
          basename = os.path.splitext( img )[0]
          ext = os.path.splitext( img )[1]
          s1 = 'src="' + wp.suburl + wp.wp_upload_dir + prefix + basename
          if wp.usescompleteurls:
               s1 = 'src="' +  wp.wp_upload_url + wp_site['testfolder'] + '/' + prefix + basename
          s2 = ext
          match = len(re.findall(s1 + "-[0-9]+x[0-9]+" + s2, content)) # content: src="/wordpress/wp-content/uploads/pythontest2/flippedDSC_1722-1024x624.webp"
          print('--- img src 1st part: ', s1)                         # s1:      src="          /wp-content/uploads/pythontest2/DSC_1722
          assert match == 1

          # compare the data-link
          # bug TODO: the data-link in the wp:galery is not being updated!
          # bug TODO: the mediaLink in the wp:image and wp:media-text : same problem, is result['link'] also
          # content: data-link="https://www.bergreisefoto.de/wordpress/dsc-1722/"
          # data-link: data-link="https://www.bergreisefoto.de/wordpress/flippeddsc_1722/
          explink = 'data-link="' + result['link']
          match = len(re.findall( explink, content) ) 
          print('--- data-link:', explink)
          assert match == 1

# TODO: check visually or programmatically that images were really changed e.g. flipped

# --------------- clean-up the WP installation
@pytest.mark.cleanup
def test_clean_up():
     # delete all created images, posts, pages
     end = len(wp.created_images)
     for i in range(0, end): 
          result = wp.delete_media( wp.created_images[i]['id'], 'media' )
          print('--- Deleted media-id: ', wp.created_images[i]['id'])
          assert result['httpstatus'] == 200
     
     # delete all created posts
     end = len(wp.created_posts)
     for i in range(0, end):
          result = wp.delete_media( wp.created_posts[i]['id'], 'posts' )
          print('--- Deleted post-id: ', wp.created_posts[i]['id'])
          assert result['httpstatus'] == 200
     
     # delete all created pages
     end = len(wp.created_pages)
     for i in range(0, end):
          result = wp.delete_media( wp.created_pages[i]['id'], 'pages' )
          assert result['httpstatus'] == 200
     
     print('Done.')

# just here for debugging the tests 
if __name__ == '__main__':
     ts = round(datetime.datetime.now().timestamp())
     test_image_upload_to_folder_with_ext_rest_api('DSC_1722.webp')
     wp.get_number_of_posts()
     #test_info_about_test_site()
     #test_get_number_of_posts_and_upload_dir()
     #test_created_json_file_list()
     #test_update_image_with_flipped_original_and_new_filename( 'DSC_1972.webp' )
     print('done')
     #test_create_gtb_gallery_with_all_images()
    