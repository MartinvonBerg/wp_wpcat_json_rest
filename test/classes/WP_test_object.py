
import requests
import json
import os.path
import magic
from helper_functions import find_plugin_in_json_resp_body, remove_html_tags, validateJSON

import os, sys

SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
#SCRIPT_DIR = os.path.join(SCRIPT_DIR, 'classes')
sys.path.append(SCRIPT_DIR)

# Class definitions for WordPress
class WP_REST_API():
    """Class with methods to access a WordPress site via the REST-API"""
    url = ''
    rest_route = ''
    wpuser = ''
    wpauth = ''
    wpversion = '0.0.0'
    themes = {}
    active_theme = {}
    plugins = {}
    active_plugins = {}
    media = { 'count' : 0 }
    pages = { 'count' : 0 }
    posts = { 'count' : 0 }
    isgutbgactive = False

    media_writeable_rest_fields = { 'title', 'gallery_sort', 'description', 'caption', 'alt_text', 'image_meta' }
    mimetypes = { 'image/webp', 'image/jpg'}

    headers = {}

    wp_upload_dir = ''

    def get_wp_version( self ): 
        self.wpversion = '5.8.0'

    def get_themes( self ):
        geturl = self.url + self.rest_route + '/themes'
        response = requests.get(geturl, headers=self.headers )
        resp_body = response.json()
        self.themes = resp_body

        pi_index = find_plugin_in_json_resp_body(resp_body, 'status', 'active')
        self.active_theme = resp_body[ pi_index]

    def get_plugins( self ):
        geturl = self.url + self.rest_route + '/plugins' 
        response = requests.get(geturl, headers=self.headers )
        resp_body = response.json()
        self.plugins = resp_body

        key = 'status'
        index = 0
        for pi in resp_body:
          if pi[key] == 'active':
              self.active_plugins[index] = pi
              if 'utenberg' in pi['name']:
                  self.isgutbgactive = True
              index += 1

    def get_number_of_posts( self, posttype='media'):
        if posttype == 'media':
            count = 0
            pagenumber = 1
            geturl = self.url + '/wp-json/wp/v2/media/?per_page=100&page='+ str(pagenumber)
            response = requests.get(geturl, headers=self.headers )
            resp_body = response.json()

            # get the (relative) upload dir of wordpress from the first media
            guid = resp_body[00]['guid']['rendered']
            base = os.path.basename(guid)
            self.wp_upload_dir = guid.replace(base, '')

            # get the maxid of images in the medialib which we assume to retrieve by the first request
            # get the minid of the first reponse, could be anywhere due to updates, even at the beginning
            allids = [d['id'] for d in resp_body]
            maxid = 0
            minid = 1000000
            for id in allids:
                if id > maxid: maxid = id
                if id < minid: minid = id

            self.media['maxid'] = maxid
                       
            # retrieve all images in the medialib 
            while len(resp_body) == 100:
                count = count + 100
                pagenumber += 1
                geturl = self.url + '/wp-json/wp/v2/media/?per_page=100&page='+ str(pagenumber)
                response = requests.get(geturl, headers=self.headers )
                resp_body = response.json()

                allids = [d['id'] for d in resp_body]
                for id in allids:
                    if id < minid: minid = id
            
            count = count + len(resp_body)
            self.media['count'] = count

            self.media['minid'] = minid

        if posttype == 'pages':
            self.pages['count'] = 0

        if posttype == 'posts':
            self.posts['count'] = 0 
    
    def __init__(self, args_in_array: dict):
        self.url = args_in_array['url']
        self.rest_route = args_in_array['rest_route']
        self.wpauth = args_in_array['authentication']
        self.headers = {
            'Authorization': self.wpauth,
            'Accept' : '*/*',
            'Accept-Encoding' : 'gzip, deflate, br',
            'Connection' : 'keep-alive',
            'User-Agent' : 'PostmanRuntime/7.28.3'
        }
        self.get_wp_version()
        self.get_themes()
        self.get_plugins()
        #self.get_number_of_posts( 'media')
        #super().__init__() # use this to call the constructor of the parent class if any
   
    def get_rest_fields( self, id: int, posttype='media', fields = {}):
        
        resp_body = {}
        resp_body['httpstatus'] = 0
        resp_body['message'] = 'Wrong id for media: not an integer above zero.'

        if isinstance(id, int) and id>0: # omitt this check for a more complete test
            keys = fields.keys()
            append = ''
            for f in keys:
                append = append + f + ','

            append = append[:-1] # remove the last ","
            geturl = self.url + '/wp-json/wp/v2/' + posttype + '/' + str(id) + '/?_fields=' + append
            response = requests.get(geturl, headers=self.headers )
            
            resp_body = response.json()
            #resp_body['_links'] = ''
            resp_body['httpstatus'] = response.status_code
            if response.status_code == 200:
                resp_body['message'] = response.reason
        
        return resp_body 

    def set_rest_fields( self, id: int, posttype='media', fields = {} ):

        resp_body = {}
        resp_body['httpstatus'] = 0
        resp_body['message'] = ''

        for f in fields:
            if f not in self.media_writeable_rest_fields:
                # only the last one will be stored
                resp_body['message'] += 'Setting of Field "' + f + '" is not allowed'
                #return

        if posttype != 'media':
            resp_body['message'] = 'Setting fields only for media allowd'
            return resp_body

        if isinstance(id, int) and id> 0:
            #
            keys = fields.keys()
            append = ''
            for f in keys:
                if f != 'image_meta':
                    append = append + f + '=' + fields[f] + '&'
                elif f == 'image_meta':
                    resp_body['message'] += 'Found image_meta but did not write it. Use seperate method'

            append = append[:-1] # remove the last "&"
            geturl = self.url + '/wp-json/wp/v2/' + posttype + '/' + str(id) + '/?' + append
            response = requests.post(geturl, headers=self.headers )
            resp_body.update( response.json() ) 
            resp_body['httpstatus'] = response.status_code
            resp_body['message'] += 'Success'
        
        else:
            resp_body['message'] += 'Wrong id for media: not an integer above zero.'
        
        return resp_body

    def add_media( self, imagefile: str ):

        resp_body = {}
        resp_body['httpstatus'] = 0
        resp_body['message'] = ''

        # check path to the image file
        isfile = os.path.isfile( imagefile )
        if not isfile:
            path = os.getcwd()
            fname = os.path.join(path, 'testdata', imagefile) 
            isfile = os.path.isfile( fname )
            if not isfile:
                return 0
        else: 
            fname = imagefile

        # read the image file to a binary string
        fin = open(fname, "rb")
        data = fin.read()
        fin.close()

        #get the base filename with extension
        imagefile = os.path.basename( fname )

        # check image mime
        mime = magic.Magic(mime=True)
        mimetype = mime.from_file(fname)
        if mimetype not in self.mimetypes:
            resp_body['message'] = 'Wrong mime type. Try it anyway.'
       
        # upload new image
        geturl = self.url + '/wp-json/wp/v2/media'
        # set the header. 
        header = self.headers
        header['Content-Disposition'] = 'form-data; filename=' + imagefile
        header['Content-Type'] = mimetype

        response = requests.post(geturl, headers=header, data=data )
        resp_body.update( json.loads( response.text) )

        # return id of the new image on success
        if response.status_code == 201:
            resp_body['httpstatus'] = response.status_code
            resp_body['message'] += response.reason
        else:
            resp_body['message'] += 'Error. Could not upload image.'

        return resp_body

    def delete_media( self, id, posttype='media' ):
        #do : http://127.0.0.1/wordpress/wp-json/wp/v2/media/3439?force=1
        
        # delete image 
        geturl = self.url + '/wp-json/wp/v2/media/' + str(id) + '?force=true'
        response = requests.delete(geturl, headers=self.headers )    
        resp_body = json.loads( response.text)
        resp_body['httpstatus'] = response.status_code
        resp_body['message'] = response.reason

        return resp_body

    def add_post( self, data: dict, posttype='post' ):
        resp_body = {}
        resp_body['httpstatus'] = 0
        resp_body['message'] = ''

        # upload new image
        if posttype == 'post':
            geturl = self.url + '/wp-json/wp/v2/posts/'
        elif posttype == 'page':
            geturl = self.url + '/wp-json/wp/v2/pages/'
        else:
            resp_body['message'] = 'wrong posttype'
            return resp_body

        header = self.headers
        header["Content-Type"] = "application/json"

        response = requests.post( geturl, headers=header, data=json.dumps(data) )
        body = json.loads( response.text)
        resp_body['httpstatus'] = response.status_code
        resp_body.update(body)

        if response.status_code == 201:
                resp_body['message'] = response.reason

        return resp_body

    def get_post_content(self, id: int, posttype='posts'):
        resp_body = {}
        resp_body['httpstatus'] = 0
        resp_body['message'] = 'Wrong id for media: not an integer above zero.'

        geturl = self.url + '/wp-json/wp/v2/' + posttype + '/' + str(id)
        response = requests.get(geturl, headers=self.headers )
        
        resp_body = response.json()
        #resp_body['_links'] = ''
        resp_body['httpstatus'] = response.status_code
        resp_body['headers'] = response.headers
        if response.status_code == 200:
            resp_body['message'] = 'OK'
        
        return resp_body

    def create_wp_image_gtb (self, id: int):
        
        fields = {}
        result = self.get_rest_fields(id, 'media', fields)
        
        altcaption = result['media_details']['image_meta']['caption']
        altcaption_from_title = result['media_details']['image_meta']['title']

        caption = result['caption']['rendered']
        if caption != '':
            caption = '<figcaption>' + result['caption']['rendered'] + '</figcaption>'

        alt = result['alt_text']
        src = result['media_details']['sizes']['full']['source_url']

        if result['httpstatus'] == 200:
             content = f'\
                <!-- wp:image {{"id":{id},"sizeSlug":"large"}} -->\
                    <figure class="wp-block-image size-large">\
                    <img src="{src}" alt="{alt}" class="wp-image-{id}"/>\
                    {caption}</figure>\
                <!-- /wp:image -->' 
        else: 
            content = 'Could not find image that was requested to generate the wp-image block!'
        
        return content

    def create_wp_media_text_gtb (self, id:int, text: str, imagewidth=50, imageFill ='false'):
        # wp:media-text does not have a caption
        fields = {}
        result = self.get_rest_fields(id, 'media', fields)
        
        alt = result['alt_text']
        #src = result['media_details']['sizes']['full']['source_url']
        src = result['media_details']['sizes']['large']['source_url']
        link = result['link']

        if result['httpstatus'] == 200:
            content = f'\
                <!-- wp:media-text {{"mediaId":{id},"mediaLink":"{link}","mediaType":"image","mediaWidth":{imagewidth},"imageFill":{imageFill}}} -->\
                    <div class="wp-block-media-text alignwide is-stacked-on-mobile" style="grid-template-columns:{imagewidth}% auto">\
                    <figure class="wp-block-media-text__media">\
                        <img src="{src}" alt="{alt}" class="wp-image-{id} size-full"/>\
                    </figure>\
                    <div class="wp-block-media-text__content">\
                    <!-- wp:paragraph {{"placeholder":"Inhalt...","fontSize":"large"}} -->\
                        <p class="has-large-font-size">{text}</p>\
                    <!-- /wp:paragraph --></div></div>\
                <!-- /wp:media-text -->' 
        else: 
            content = 'Could not find image that was requested to generate the wp-image block!'
        
        return content

    def create_wp_gallery_gtb( self, ids={}, columns=2, galcaption = ''):
        fields = {}
        idsstring = ",".join( ids.values() )
        content = ''
        columens = str(columns)
        if galcaption == '':
            galcaption = 'No Caption for the Galery provided.'
        

        for id in ids.values():
            result = self.get_rest_fields( int(id), 'media', fields)

            # check http status, skip if not 200 and remove id from idsstring
            if result['httpstatus'] == 200:
                alt = result['alt_text']
                srcfull = result['media_details']['sizes']['full']['source_url']
                try:
                    src = result['media_details']['sizes']['large']['source_url']
                except:
                    src = result['media_details']['sizes']['full']['source_url']

                link = result['link']

                caption = result['caption']['rendered']
                caption = remove_html_tags( caption )
                if caption == '':
                    caption = 'No Caption found'
                 
                content += f'\
                            <li class="blocks-gallery-item">\
                            <figure><img src="{src}" alt="{alt}" data-id="{id}" data-full-url="{srcfull}"\
                                data-link="{link}" class="wp-image-{id}" />\
                                <figcaption class="blocks-gallery-item__caption">{caption}</figcaption>\
                            </figure></li>'
            
            else:
                idsstring = idsstring.replace( id + ',', '')
                idsstring = idsstring.replace( id, '')
             
        contentbefore= f'<!-- wp:gallery {{"ids":[{idsstring}],"columns":{columns},"linkTo":"none"}} -->\
                    <figure class="wp-block-gallery columns-{columns} is-cropped">\
                    <ul class="blocks-gallery-grid">'    

        content = contentbefore + content    
        
        content += f'</ul><figcaption class="blocks-gallery-caption">{galcaption}</figcaption>\
                    </figure><!-- /wp:gallery -->'
        
        return content

class WP_EXT_REST_API( WP_REST_API ):
    """Extend the class WP_REST_API with methods for the plugin that
    extendeds the REST-API of WordPress to update images and add images 
    to dedicated folders."""
    tested_plugin_dir = 'wp-wpcat-json-rest/wp_wpcat_json_rest'
    tested_plugin_name = 'Ext_REST_Media_Lib'
    tested_plugin_min_version = '0.0.14'
    tested_plugin_version = ''
    tested_plugin_activated = False
    created_images = {}
    created_posts = {}
    created_pages = {}
    tested_site = {}
    last_media_id = 0
    last_index_in_created_images = 0

    def get_tested_plugin ( self ):
        """ Get some information about the tested plugin."""
        self.tested_plugin_version = ''
        index = find_plugin_in_json_resp_body( self.plugins, 'name', self.tested_plugin_name)
        self.tested_plugin_version = self.plugins[index]['version']
        if self.plugins[index]['status'] == 'active':
            self.tested_plugin_activated = True

    def __init__(self, args_in_array):
        super().__init__( args_in_array )
        self.tested_site = args_in_array
        self.get_tested_plugin()

    def set_attachment_image_meta( self, id: int, posttype= 'media', fields = {} ):
        """ Write the image_meta given in fields via REST-API Extension to WordPress. 
        Othe values than image_meta are silently ignored."""
        resp_body = {}
        resp_body['httpstatus'] = 0
        resp_body['message'] = ''

        for f in fields:
            if f not in self.media_writeable_rest_fields:
                resp_body['message'] = 'Setting of Field "' + f + '" is not allowed'

        if posttype != 'media':
            resp_body['message'] = 'Setting fields only for media allowd'
            return resp_body

        if isinstance(id, int) and id> 0:
            #
            keys = fields.keys()    

            for f in keys:           
                if f == 'image_meta':
                    # localhost/wordpress/wp-json/extmedialib/v1/update_meta/5866?docaption=true
                    geturl = self.url + '/wp-json/extmedialib/v1/update_meta/' + str(id) + '?docaption=true'
                    piece = {}
                    piece['image_meta'] = fields['image_meta']
                    body = json.dumps(piece) 

                    isvalidjson = validateJSON( body )

                    if not isvalidjson:
                        resp_body['message'] += 'Invalid JSON body in preparation of POST-Request'

                    header = self.headers    
                    header['Content-Type'] = "application/json"
                    response = requests.post(geturl, headers=header, data=body )
                    resp_body.update( response.json() )
                    resp_body['httpstatus'] = response.status_code
            
            if resp_body['message'] == '':
                resp_body['message'] = 'Field image_meta was not provided. No REST-request done.'

        else:
            resp_body['message'] += 'Wrong id for media: not an integer above zero.'
        
        return resp_body

    def get_update_image( self, id: int ):
        """ Call the GET-method of route 'update' of REST-API Extension"""
        resp_body = {}
        resp_body['httpstatus'] = 0
        resp_body['message'] = ''

        # upload new image
        geturl = self.url + '/wp-json/extmedialib/v1/update/' + str(id)
        
        response = requests.get(geturl, headers=self.headers )
        resp_body.update( json.loads( response.text) )

        # return id of the new image on success
        if response.status_code == 200:
            resp_body['httpstatus'] = response.status_code
        
        return resp_body

    def post_update_image( self, id: int, imagefile: str, changemime=True ):
        """ Call the POST-method of route 'update' of REST-API Extension. Update the image 
        with the provided path to the imagefile. Update meta-data seperately."""
        resp_body = {}
        resp_body['httpstatus'] = 0
        resp_body['message'] = ''

        # check path to the image file
        isfile = os.path.isfile( imagefile )
        if not isfile:
            path = os.getcwd()
            fname = os.path.join(path, 'testdata', imagefile) 
            isfile = os.path.isfile( fname )
            if not isfile:
                resp_body['message'] = 'File not found'
                return resp_body
        else: 
            fname = imagefile

        # read the image file to a binary string
        fin = open(fname, "rb")
        data = fin.read()
        fin.close()

        #get the base filename with extension
        imagefile = os.path.basename( fname )

        # check image mime
        mime = magic.Magic(mime=True)
        mimetype = mime.from_file(fname)
        if mimetype not in self.mimetypes:
            resp_body['message'] = 'Wrong mime type. Try it anyway.'
       
        # upload new image
        geturl = self.url + '/wp-json/extmedialib/v1/update/' + str(id)
        if changemime:
            geturl += '?changemime=true'
       
        # set the header. 
        header = self.headers
        header['Content-Disposition'] = 'form-data; filename=' + imagefile
        header['Content-Type'] = mimetype

        response = requests.post(geturl, headers=header, data=data )
        resp_body.update( json.loads( response.text) )

        # return id of the new image on success
        if response.status_code == 200:
            resp_body['httpstatus'] = response.status_code
        
        else:
            resp_body['message'] += 'Error. Could not update image.'

        return resp_body
       
    def get_add_image_to_folder( self, folder: str ):
        """ Call the GET-method of route 'addtofolder' of REST-API Extension."""
        resp_body = {}
        resp_body['httpstatus'] = 0
        resp_body['message'] = ''

        # upload new image
        geturl = self.url + '/wp-json/extmedialib/v1/addtofolder/' + folder
        
        response = requests.get(geturl, headers=self.headers )
        resp_body.update( json.loads( response.text) )

        # return id of the new image on success
        resp_body['httpstatus'] = response.status_code
        
        return resp_body

    def post_add_image_to_folder( self, folder: str, imagefile: str ):
        """ Call the POST-method of route 'addtofolder' of REST-API Extension and add
        the provided imagefile to the folder under ../uploads in WordPress. Similar to
        method 'add_media' of the Base-Class but adds the image to a dedicated folder."""
        resp_body = {}
        resp_body['httpstatus'] = 0
        resp_body['message'] = ''

        # check path to the image file
        isfile = os.path.isfile( imagefile )
        if not isfile:
            path = os.getcwd()
            fname = os.path.join(path, 'testdata', imagefile)
            print('Upload File: ', fname)
            isfile = os.path.isfile( fname )
            if not isfile:
                resp_body['message'] = 'Cannot find file'
                return resp_body
        else: 
            fname = imagefile

        # read the image file to a binary string
        fin = open(fname, "rb")
        data = fin.read()
        fin.close()

        #get the base filename with extension
        imagefile = os.path.basename( fname )

        # check image mime
        mime = magic.Magic(mime=True)
        mimetype = mime.from_file(fname)
        if mimetype not in self.mimetypes:
            resp_body['message'] = 'Wrong mime type. Try it anyway.'
       
        # upload new image
        geturl = self.url + '/wp-json/extmedialib/v1/addtofolder/' + folder
        # set the header. 
        header = self.headers
        header['Content-Disposition'] = 'attachment; filename=' + imagefile
        header['Content-Type'] = mimetype

        response = requests.post(geturl, headers=header, data=data )
        resp_body.update( json.loads( response.text) )

        # return id of the new image on success
        resp_body['httpstatus'] = response.status_code
        #resp_body['message'] += response.reason
       
        return resp_body
      
    # ------ This methodes are currently not implemented and therefore not tested
    def get_add_image_from_folder( self ):
        method = 'get'
        return 0

    def post_add_image_from_folder( self ):
        method = 'post'
        return 0    
# End of Class