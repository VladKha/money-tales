import logging
from datetime import datetime
from typing import Dict
import xml.etree.ElementTree as ET
from xml.dom import minidom

from dotenv import load_dotenv

try:
    from src.db import AlibabaCloudOSSStorageDB
except ImportError:
    from db import AlibabaCloudOSSStorageDB


# Load environment variables from .env file
load_dotenv()

# Configure logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_story_info(story_path: str, db: AlibabaCloudOSSStorageDB) -> Dict:
    """Extract story information from the story file path and content."""
    # Get the story content
    story_content = db.get_file(story_path)
    title = story_content.split('\n\n')[0]
    content = '\n\n'.join(story_content.split('\n\n')[1:])
    
    # Extract timestamp from path
    guid = story_path.split('/')[0]
    timestamp = '_'.join(guid.split('_')[-2:])  # Format: YYYYMMDD_HHMMSS
    pub_date = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
    
    # Find corresponding audio file
    audio_url = db.get_file_url(story_path.replace('.txt', '.mp3'))
    
    return {
        'title': title,
        'content': content,
        'pub_date': pub_date,
        'audio_url': audio_url,
        'guid': guid,
    }

def generate_rss_feed(oss_storage: AlibabaCloudOSSStorageDB, output_file: str = 'rss_feed.xml'):
    """Generate RSS feed XML file from OSS storage content."""
    # List all stories
    stories = oss_storage.list_files()
    
    # Filter and sort stories
    story_files = [s for s in stories if s.endswith('.txt')]
    story_files.sort(reverse=True)  # Sort by timestamp in descending order
    
    # Create RSS root
    rss = ET.Element('rss', version='2.0')
    rss.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
    rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
    
    # Create channel
    channel = ET.SubElement(rss, 'channel')
    
    # Add channel metadata
    ET.SubElement(channel, 'title').text = 'MoneyTales'
    ET.SubElement(channel, 'language').text = 'en-en'
    ET.SubElement(channel, 'copyright').text = '© 2025 MoneyTales'
    ET.SubElement(channel, 'itunes:subtitle').text = 'Financial literacy for kids with fictional stories'
    ET.SubElement(channel, 'itunes:author').text = 'Super Podcaster'
    ET.SubElement(channel, 'itunes:summary').text = 'Financial literacy for kids with fictional stories'
    ET.SubElement(channel, 'description').text = 'Financial literacy for kids with fictional stories'
    ET.SubElement(channel, 'webMaster').text = 'Super Podcaster'
    
    # Add itunes:owner
    owner = ET.SubElement(channel, 'itunes:owner')
    ET.SubElement(owner, 'itunes:name').text = 'Super Podcaster'
    ET.SubElement(owner, 'itunes:email').text = ''
    
    # Add itunes:image
    image = ET.SubElement(channel, 'itunes:image')
    image.set('href', oss_storage.logo_url)
    
    # Add itunes:category
    category = ET.SubElement(channel, 'itunes:category')
    category.set('text', 'Education')
    subcategory = ET.SubElement(category, 'itunes:category')
    subcategory.set('text', 'Self-Improvement')
    
    ET.SubElement(channel, 'itunes:explicit').text = 'No'
    
    # Add items for each story
    for i, story_path in enumerate(story_files, 1):
        try:
            story_info = get_story_info(story_path, oss_storage)
            
            item = ET.SubElement(channel, 'item')
            ET.SubElement(item, 'title').text = f'{story_info["title"]}'
            ET.SubElement(item, 'itunes:author').text = 'Super Podcaster'
            ET.SubElement(item, 'itunes:subtitle').text = story_info['title']
            ET.SubElement(item, 'itunes:summary').text = story_info['content'][:200] + '...'
            ET.SubElement(item, 'description').text = story_info['content']
            
            # Add itunes:image
            # image = ET.SubElement(item, 'itunes:image')
            # image.set('href', 'https://your-domain.com/images/logo.png') # TODO
            
            # Add enclosure
            enclosure = ET.SubElement(item, 'enclosure')
            enclosure.set('url', story_info['audio_url']) #f'https://{oss_storage.bucket_name}.{oss_storage.endpoint.replace("https://", "")}/{story_info["audio_path"]}')
            enclosure.set('type', 'audio/mpeg')
            
            # Add guid
            guid = ET.SubElement(item, 'guid')
            guid.set('isPermaLink', 'false')
            guid.text = story_info['guid']
            
            # Add pubDate
            ET.SubElement(item, 'pubDate').text = story_info['pub_date'].strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            # Add itunes:duration (placeholder - you might want to calculate actual duration)
            # ET.SubElement(item, 'itunes:duration').text = '00:05:00'
            
            ET.SubElement(item, 'itunes:explicit').text = 'No'

        except Exception as e:
            logging.error(f"Error processing story {story_path}: {e}")
            continue
    
    # Convert to pretty XML
    xmlstr = minidom.parseString(ET.tostring(rss)).toprettyxml(indent="  ")
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xmlstr)
    
    logging.info(f"RSS feed generated successfully: {output_file}")
    return xmlstr


if __name__ == "__main__":
    db = AlibabaCloudOSSStorageDB()
    output_file = 'rss_feed.xml'
    rss_content = generate_rss_feed(db, output_file)
    db.save_to_file(rss_content, output_file)
