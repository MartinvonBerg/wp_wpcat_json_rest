<?php
namespace mvbplugins\extmedialib;

defined( 'ABSPATH' ) || die( 'Not defined' );

/**
 * Callback for GET to REST-Route 'update/<id>'. Check wether Parameter id (integer!) is an WP media attachment, e.g. an image and calc md5-sum of original file
 *
 * @param array{id:int} $data is the complete Request data of the REST-api GET
 * @return \WP_REST_Response|WP_Error array for the rest response body or a WP Error object
 */
function get_image_update( $data )
{
	$post_id = $data['id'];
	$att = wp_attachment_is_image($post_id);
	$resized = wp_get_attachment_image_src($post_id, 'original');

	if ( 'array' == \gettype( $resized ) )
		$resized = $resized[3];
		
	if ($att && (! $resized)) {
		$original_filename = wp_get_original_image_path($post_id);
		if (false == $original_filename) $original_filename = '';
		
		if (is_file( $original_filename )) {
			$md5 = strtoupper( (string) md5_file( $original_filename ) );
		} else {
			$md5 = 0;
		}
		$getResp = array(
			'message' => 'You requested update of original Image with ID '. $post_id . ' with GET-Method. Please update with POST-Method.',
			'original-file' => $original_filename,
			'md5_original_file' => $md5,
			'max_upload_size' => (string)wp_max_upload_size() . ' bytes'
		);
	} elseif ($att && $resized) {
		$file2 = get_attached_file($post_id, true);
		$getResp = array(
			'message' => 'Image ' . $post_id . ' is a resized image',)
			;
	} else {
		return new \WP_Error('no_image', 'Invalid Image of any type: ' . $post_id, array( 'status' => 404 ));
	};

	return rest_ensure_response ( $getResp );
};

/**
 * Callback for POST to REST-Route 'update/<id>'. Update attachment with Parameter id (integer!). 
 * This function updates the image FILE only and the filename if provided. If the old title of the 
 * image was different from the filename this title will be kept. All other meta-data remains unchanged!
 * Important Source: https://developer.wordpress.org/reference/classes/wp_rest_request
 *
 * @param object $data is the complete Request data of the REST-api GET
 * @return \WP_REST_Response|WP_Error array for the rest response body or a WP Error object
 */
function post_image_update( $data )
{
	global $wpdb;

	include_once ABSPATH . 'wp-admin/includes/image.php';
	$minsize   = MIN_IMAGE_SIZE;
	$post_id = $data['id'];
	$att = wp_attachment_is_image($post_id);
	$dir = wp_upload_dir()['basedir'];
	$image = $data->get_body(); // body as string (=jpg-image) of POST-Request
	$postRequestFileName = explode( ';', $data->get_headers()['content_disposition'][0] )[1];
	$postRequestFileName = trim( \str_replace('filename=', '', $postRequestFileName) );
	$postRequestFileName = \sanitize_file_name( $postRequestFileName );
			
	if ( ($att) && (strlen($image) > $minsize) && (strlen($image) < wp_max_upload_size()) ) {
		// get current metadata from WP-Database
		$meta = wp_get_attachment_metadata($post_id);
		$wpmediadata = get_post( $post_id, 'ARRAY_A'); 
		if ( false == $meta ) { $meta = array(); }
		$oldlink = get_attachment_link( $post_id ); // identical to old permalink
		
		// Define filenames in different ways for the different functions
		$fileName_from_att_meta = $meta['file'];
		$dir = \str_replace('\\','/',$dir);
		$checker = \str_replace($dir,'',$fileName_from_att_meta);
		if ($checker[0] != '/') {
			$fileName_from_att_meta = $dir . '/' . $checker;
		}
		
		$old_original_fileName = str_replace( '-' . EXT_SCALED, '', $fileName_from_att_meta); // This is used to save the POST-body
		$ext = '.' . pathinfo($old_original_fileName)['extension']; // Get the extension
		$old_original_fileName = set_complete_path($dir, $old_original_fileName);
		$filename_for_deletion = str_replace($ext, '', $old_original_fileName); // Filename without extension for the deletion with Wildcard '*'
		

		// data for the REST-response
		$base_fileName_from_att_meta = basename($fileName_from_att_meta); // filename with extension with '-scaled'
		$original_filename_old_file = str_replace('-' . EXT_SCALED, '', $base_fileName_from_att_meta);
		$old_upload_dir = str_replace( $base_fileName_from_att_meta, '', $fileName_from_att_meta ); // This is the upload dir that was used for the original file $old_upload_dir = str_replace( $original_filename_old_file, '', $old_attached_file );
		$dir = str_replace('\\', '/', $dir ); 
		$old_upload_dir = str_replace('\\', '/', $old_upload_dir );
		$gallerydir = str_replace($dir, '', $old_upload_dir);
		$gallerydir = trim($gallerydir, '/\\');

		// get parent and permalink
		$oldParent = \wp_get_post_parent_id( $post_id);

		// call the media replacer class with construct-method of the class to get basic information about the attachment-image
		$replacer = new \mvbplugins\extmedialib\Replacer( $post_id );
		
		// generate the filename for the new file
		if ( $postRequestFileName == '' ) {
			// if provided filename is empty : use the old filename
			$path_to_new_file = set_complete_path($dir, $old_original_fileName);
			// keep the old title in case no filename is given
			$new_post_title = $wpmediadata["post_title"];
			
		} else {
			// generate the complete path for the new uploaded file
			//$path_to_new_file = $old_upload_dir . $postRequestFileName;
			$path_to_new_file = $dir . \DIRECTORY_SEPARATOR . $gallerydir . \DIRECTORY_SEPARATOR . $postRequestFileName;

			$old_basename_without_extension = \str_replace( $ext, '', $base_fileName_from_att_meta); 
			if ( \str_replace( $ext, '', $wpmediadata["post_title"]) == $old_basename_without_extension) {
				$new_post_title = pathinfo( $postRequestFileName )['filename'];
			} else {
				$new_post_title = $wpmediadata["post_title"];
			} 
		}
		$path_to_new_file = str_replace('\\', '/', $path_to_new_file );

		// save old Files before, to redo them if something goes wrong
		//function filerename($fileName_from_att_meta) {
		//	rename($fileName_from_att_meta, $fileName_from_att_meta . '.oldimagefile');
		//	if ( ! \is_file( $fileName_from_att_meta . '.oldimagefile' )) $add = 'at least one file not renamed!';
		//}
		$filearray = glob($filename_for_deletion . '*');
		//array_walk($filearray, '\mvbplugins\extmedialib\filerename');

		array_walk($filearray, function( $fileName_from_att_meta ){
			rename($fileName_from_att_meta, $fileName_from_att_meta . '.oldimagefile');
		} );
		
		// check if file exists alreay, don't overwrite
		$fileexists = \is_file( $path_to_new_file );
		if ( $fileexists ) {
			$old_attached_file_before_update = get_attached_file($post_id, true);
			$getResp = array(
				'message' => __('You requested upload of file') . ' '. $postRequestFileName . ' ' . __('with POST-Method'),
				'Error_Details' => __('Path') . ': ' . $path_to_new_file,
				'file6' => 'filebase for rename: ' . $filename_for_deletion,
				'old' => 'old attach: ' . $old_attached_file_before_update,
				'dir' => 'Variable $dir: ' . $dir,
			);
			$newGetResp = \implode(' , ', $getResp);
			return new \WP_Error( __('File exists'), $newGetResp, array( 'status' => 409 ));
		}

		// Save new file from POST-body and check MIME-Type
		$success_new_file_write = file_put_contents( $path_to_new_file, $image );
		
		// check the new file type and extension
		$changemime = $data->get_params()['changemime'] == 'true' ? true : false;
		$newfile_mime = wp_get_image_mime( $path_to_new_file );
		$new_mime_from_header = $data->get_content_type()['value']; // upload content-type of POST-Request
		$new_File_Extension = pathinfo( $path_to_new_file )['extension'];
		$wp_allowed_mimes = \get_allowed_mime_types();
		$wp_allowed_ext = array_search( $newfile_mime, $wp_allowed_mimes, false);
		$new_ext_matches_mime = stripos( $wp_allowed_ext, $new_File_Extension)>-1 ? true : false;
		$new_File_Extension = '.' . $new_File_Extension;
		$new_File_Name  = pathinfo( $path_to_new_file )['filename'];

		// mime type of the old attachment
		$old_mime_from_att = get_post_mime_type( $post_id ) ;

		if ( ! $changemime ) {
			$all_mime_ext_OK = ($newfile_mime == $old_mime_from_att) && ($newfile_mime == $new_mime_from_header) && ($ext == $new_File_Extension) && $new_ext_matches_mime;
		} else {
			$all_mime_ext_OK = ($newfile_mime == $new_mime_from_header) && $new_ext_matches_mime;
		}
		
		if ( $all_mime_ext_OK ) {

			// resize missing images
			$att_array = array(
				'ID'			 => $post_id,
				 //'guid'           => $path_to_new_file, // works only this way -- use a relative path to ... /uploads/ - folder
				'guid'			 => $gallerydir . '/' . $new_File_Name . $new_File_Extension,
				'post_mime_type' => $newfile_mime, // e.g.: 'image/jpg'
				'post_title'     => $new_post_title, // this creates the title and the permalink, if post_name is empty
				'post_content'   => $wpmediadata["post_content"],
				'post_excerpt'   => $wpmediadata["post_excerpt"],
				'post_status'    => 'inherit',
				'post_parent'	 => $oldParent, // int
				'post_name' 	 => '' , // this is used for Permalink :  https://example.com/title-88/, (if empty post_title is used)
			);
			
			// update the attachment = image with standard methods of WP
			wp_insert_attachment( $att_array, $gallerydir . '/' . $new_File_Name . $new_File_Extension, 0, true, false );
			$success_subsizes = wp_create_image_subsizes( $path_to_new_file, $post_id ); // nach dieser Funktion ist der Dateiname falsch! Nur dann wenn größer als big-image-size!
			
			// update post doesn't update GUID on updates. guid has to be the full url to the file
			$url_to_new_file = get_upload_url() . '/' . $gallerydir . '/' . $new_File_Name . $new_File_Extension;
			$wpdb->update( $wpdb->posts, array( 'guid' =>  $url_to_new_file ), array('ID' => $post_id) );
			update_post_meta($post_id, '_wp_attached_file', $gallerydir . '/' . $new_File_Name . $new_File_Extension); // mit dieser Funktion wird er wieder korrigiert


			// set the meta and the caption back to the original values. Absichtlich? Das Bild kann ein völlig anderes sein.
			// Die Metadaten müssen getrennt gesetzt werden, steht doch auch so in der Anleitung.
			// Diese Funktion aktualisiert nur das Bild, nicht die Metadaten!
			
			//update the posts that use the image with class from plugin enable_media_replace
			// This updates only the image url that are used in the post. The metadata e.g. caption is NOT updated.
			$replacer->new_location_dir = $gallerydir;
			$replacer->set_oldlink( $oldlink );
			$newlink = get_attachment_link( $post_id ); // get_attachment_link( $post_id) ist hier bereits aktualisiert
			$replacer->set_newlink( $newlink );
			$replacer->target_url = $url_to_new_file;
			$replacer->target_metadata = $success_subsizes;
			$replacer->API_doSearchReplace();
			$replacer = null;

		} else {
			$success_subsizes = 'Check-Mime-Type mismatch';
		}
				
		if (($success_new_file_write != false) && (is_array($success_subsizes))) {
			$getResp = array(
				'id' => $post_id,
				'message' => __('Successful update. Except Metadata.'),
				'old_filename' => $original_filename_old_file,
				'new_fullpath' => $path_to_new_file,
				'gallery' => $gallerydir,
				'Bytes written' => $success_new_file_write,
				);
			
			// delete old files
			array_map("unlink", glob($filename_for_deletion . '*oldimagefile'));

		} else {
			// something went wrong redo the change, recover the old files
			if (is_array($success_subsizes)) {
				$success_subsizes = __('Was OK');
			} elseif (! is_string($success_subsizes)) {
				$success_subsizes = implode($success_subsizes->get_error_messages());
			};

			$success_new_file_write = array(
				'message' => __('ERROR. Something went wrong. Original files not touched.'),
				'new_file_write' => (string)$success_new_file_write,
				'gen_subsizes' => $success_subsizes,
			);

			$getResp = array(
				'message' => __('You requested update with POST-Method of') . ' ID: '. $post_id,
				'Error_Details' => $success_new_file_write,
			);

			// recover the original files if something went wrong
			//function recoverfile( $fileName_from_att_meta ) {
			//	rename($fileName_from_att_meta, str_replace('.oldimagefile', '', $fileName_from_att_meta));
			//}
			$filearray = glob($filename_for_deletion . '*oldimagefile');
			//array_walk($filearray, '\mvbplugins\extmedialib\recoverfile');

			array_walk( $filearray, function( $fileName_from_att_meta ) {
				rename( $fileName_from_att_meta, str_replace('.oldimagefile', '', $fileName_from_att_meta ) );
			} );

			// delete the file that was uploaded by REST - POST request
			unlink($old_original_fileName);
			$newGetResp = \implode(' , ', $getResp);
			return new \WP_Error('Error', $newGetResp, array( 'status' => 400 ));
		}
		
	} elseif (($att) && (strlen($image) < $minsize)) {
		return new \WP_Error('too_small', 'Invalid Image (smaller than: '. $minsize .' bytes) in body for update of: ' . $post_id, array( 'status' => 400 ));
	} elseif (($att) && (strlen($image) > wp_max_upload_size())) {
		return new \WP_Error('too_big', 'Invalid Image (bigger than: '. wp_max_upload_size() .' bytes) in body for update of: ' . $post_id, array( 'status' => 400 ));
	} elseif (! $att) {
		return new \WP_Error('not_found', 'Attachment is not an Image: ' . $post_id, array( 'status' => 415 ));
	}
	
	return rest_ensure_response($getResp);
};