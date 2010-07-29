from PMS import Plugin, Log, XML, HTTP, JSON, Prefs
from PMS.MediaXML import MediaContainer, DirectoryItem, VideoItem, SearchDirectoryItem
from PMS.Shorthand import _L, _E, _D

IGN_PREFIX             = "/video/ign"

URL_HOME               = "http://video.ign.com/"
URL_ALL                = "http://www.ign.com/index/videos.html"
URL_VIDEO_SERIES       = "http://video.ign.com/index/videoseries.html"

CACHE_INT_HOME         = 1800   # 30 Minutes
CACHE_INT_VIDEO_PAGE   = 604800 # 1 Week
CACHE_INT_SERIES_LIST  = 604800 # 1 Week
CACHE_INT_VIDEO_SERIES = 86400  # 1 Day
CACHE_INT_RECENT       = 86400  # 1 Day

LIMIT_SERIES_EPISODES  = 7 # 8 rows in MediaStream List mode, leaves room for All Episodes option

TEXT_IGN               = _L("ign")
TEXT_TOP_VIDEOS        = _L("topVideos")
TEXT_LATEST_VIDEOS     = _L("latestVideos")
TEXT_GAME_TRAILERS     = _L("gameTrailers")
TEXT_MOVIE_TRAILERS    = _L("movieTrailers")
TEXT_REVIEWS           = _L("reviews")
TEXT_PREVIEWS          = _L("previews")
TEXT_VIDEO_SERIES      = _L("videoSeries")
TEXT_ALL_SERIES        = _L("allSeries")
TEXT_ALL_EPISODES      = _L("allEpisodes")
TEXT_HIT_LIST          = _L("hitList")
TEXT_RECENT_VIDEOS     = _L("recentVideos")
TEXT_ALL_VIDEOS        = _L("allVideos")
TEXT_INSIDER_IND       = "[" + _L("insider") + "]"

PATH_TOP_VIDEOS        = "top"
PATH_LATEST_VIDEOS     = "latest"
PATH_GAME_TRAILERS     = "gameTrailers"
PATH_MOVIE_TRAILERS    = "movieTrailers"
PATH_REVIEWS           = "reviews"
PATH_PREVIEWS          = "previews"
PATH_VIDEO_SERIES      = "videoSeries"
PATH_HIT_LIST          = "hitList"
PATH_RECENT_VIDEOS     = "recent"
PATH_ALL_VIDEOS        = "all"

FILE_DEFAULT_ART       = "art-default.jpg"
FILE_DEFAULT_ICON      = "icon-default.png"

XPATH_TOP_VIDEOS         = '//div[@id="video_top_stories"]//div[@class="slider_wrapper"]/ul/li'
XPATH_LATEST_VIDEOS      = '//div[@id="latest_videos"]//tr[contains(@class, "lv-item")]//a'
XPATH_GAME_TRAILERS      = '//div[@id="game_trailers"]//div[@class="thumb_div has_play"]/a'
XPATH_MOVIE_TRAILERS     = '//div[@id="movie_trailers"]//div[@class="thumb_div has_play"]/a'
XPATH_REVIEWS            = '//div[@id="reviews"]//div[@class="thumb_div has_play"]/a'
XPATH_PREVIEWS           = '//div[@id="previews"]//div[@class="thumb_div has_play"]/a'
XPATH_VIDEO_SERIES       = '//div[@id="video_series"]//div[@class="thumb_div"]/a'
XPATH_VIDEO_SERIES_EP    = '//div[contains(@class, "thumb_div")]'
XPATH_ALL_VIDEO_SERIES   = XPATH_VIDEO_SERIES_EP
XPATH_HIT_LIST           = '//div[@id="col_hot_topics"]//ul/li/a'
XPATH_SELECTED_HIT       = '//div[@class="hub_box3_layer"][%s]//div[contains(@class, "thumb_div")]'
XPATH_RECENT_VIDEOS      = 'id("colCenterSectionIndex")//tr'
XPATH_RECENT_VIDEOS_PAGE = '//div[contains(@class, "thumb_div")]/a'

def Start():
  Plugin.AddRequestHandler(IGN_PREFIX, HandleRequest, TEXT_IGN, FILE_DEFAULT_ICON, FILE_DEFAULT_ART)

def LoadUrl(url, cacheInt):
  xml = XML.ElementFromString(HTTP.GetCached(url, cacheInt), True) # This may cache the interstitial ad page
  while len(xml.xpath('//a[@class="prestitialText2"]')) != 0:
    xml = XML.ElementFromURL(url, True) # Is there a way to refresh the cache?
  
  return xml
  
def HomePageXml():
  return LoadUrl(URL_HOME, CACHE_INT_HOME)

def CreateVideoItemFromPage(url, thumbUrl=None, desc="", title=None):
  videoPageXml = LoadUrl(url, CACHE_INT_VIDEO_PAGE)
  if title == None:
    title = videoPageXml.xpath('//h1')[0].text
  
  # Parse JavaScript which contains direct URL to Flash video
  rawSrc = videoPageXml.xpath('//script/text()')[1]
  begin = rawSrc.find("hiResFlash = '") + 14 # TODO Add option for low/hi res here
  end = rawSrc.find(".flv';") + 4
  end += rawSrc[end:].find(".flv") + 4
  flv = "http://" + rawSrc[begin:end]
  
  # Might be Insider content
  if url.find("insider.ign.com") >= 0:
    title = TEXT_INSIDER_IND + " " + title
  
  return VideoItem(flv, title, desc, "", thumbUrl)

def SimpleHomePagePlaylist(query, title):
  dir = MediaContainer(FILE_DEFAULT_ART, title1=TEXT_IGN, title2=title)
  
  for video in HomePageXml().xpath(query):
    videoPage = video.get("href")
    thumbUrl = video.find("img").get("src")
    dir.AppendItem(CreateVideoItemFromPage(videoPage, thumbUrl))
  
  return dir.ToXML()

def Index():
  dir = MediaContainer(FILE_DEFAULT_ART, title1=TEXT_IGN)
  
  xml = HomePageXml()
  
  # "Exclusive" video is not always there
  exclusiveLinks = xml.xpath('//div[@id="video_exclusive"]//a')
  if len(exclusiveLinks) > 1:
    videoPage = exclusiveLinks[1].get("href")
    thumbUrl = xml.xpath('//div[@id="video_exclusive"]//a[1]/img')[0].get("src")
    dir.AppendItem(CreateVideoItemFromPage(videoPage, thumbUrl))
  
  dir.AppendItem(DirectoryItem(PATH_TOP_VIDEOS,     TEXT_TOP_VIDEOS,     ""))
  dir.AppendItem(DirectoryItem(PATH_LATEST_VIDEOS,  TEXT_LATEST_VIDEOS,  ""))
  dir.AppendItem(DirectoryItem(PATH_VIDEO_SERIES,   TEXT_VIDEO_SERIES,   ""))
  dir.AppendItem(DirectoryItem(PATH_HIT_LIST,       TEXT_HIT_LIST,       ""))
  dir.AppendItem(DirectoryItem(PATH_GAME_TRAILERS,  TEXT_GAME_TRAILERS,  ""))
  dir.AppendItem(DirectoryItem(PATH_MOVIE_TRAILERS, TEXT_MOVIE_TRAILERS, ""))
  dir.AppendItem(DirectoryItem(PATH_REVIEWS,        TEXT_REVIEWS,        ""))
  dir.AppendItem(DirectoryItem(PATH_PREVIEWS,       TEXT_PREVIEWS,       ""))
  dir.AppendItem(DirectoryItem(PATH_RECENT_VIDEOS,  TEXT_RECENT_VIDEOS,  ""))
  
  return dir.ToXML()

def TopVideos():
  dir = MediaContainer(FILE_DEFAULT_ART, title1=TEXT_IGN, title2=TEXT_TOP_VIDEOS)
  
  for video in HomePageXml().xpath(XPATH_TOP_VIDEOS):
    videoPage = video.find('div/a').get("href")
    thumbUrl = video.find('div/a/img').get("src")
    dir.AppendItem(CreateVideoItemFromPage(videoPage, thumbUrl))
  
  return dir.ToXML()

def Latest():
  dir = MediaContainer(FILE_DEFAULT_ART, title1=TEXT_IGN, title2=TEXT_LATEST_VIDEOS)
  
  for video in HomePageXml().xpath(XPATH_LATEST_VIDEOS):
    videoPage = video.get("href")
    # Latest Videos are just a list, no thumbs
    dir.AppendItem(CreateVideoItemFromPage(videoPage))
  
  return dir.ToXML()

def GameTrailers():
  return SimpleHomePagePlaylist(XPATH_GAME_TRAILERS, TEXT_GAME_TRAILERS)

def MovieTrailers():
  return SimpleHomePagePlaylist(XPATH_MOVIE_TRAILERS, TEXT_MOVIE_TRAILERS)
  
def Reviews():
  return SimpleHomePagePlaylist(XPATH_REVIEWS, TEXT_REVIEWS)

def Previews():
  return SimpleHomePagePlaylist(XPATH_PREVIEWS, TEXT_PREVIEWS)

def VideoSeries(all=False):
  dir = MediaContainer(FILE_DEFAULT_ART, title1=TEXT_IGN, title2=TEXT_VIDEO_SERIES)

  if all: # From Video Series page
    for series in LoadUrl(URL_VIDEO_SERIES, CACHE_INT_SERIES_LIST).xpath(XPATH_ALL_VIDEO_SERIES):
      thumb = series.find("a/img").get("src")
      title = series.find("a/img").get("alt")
      url = series.find("a").get("href")
      dir.AppendItem(DirectoryItem(_E(url) + "||" + _E(title), title, thumb))
      
  else: # From Home page
    for series in HomePageXml().xpath(XPATH_VIDEO_SERIES):
      url = series.get("href")
      name = series.find("img").get("alt")
      thumb = series.find("img").get("src")
      dir.AppendItem(DirectoryItem(_E(url) + "||" + _E(name), name, thumb))
    dir.AppendItem(DirectoryItem("all", TEXT_ALL_SERIES, None))
  
  return dir.ToXML()

def SelectedVideoSeries(url, title, limit=9999):  
  dir = MediaContainer(FILE_DEFAULT_ART, title1=TEXT_IGN, title2=_D(title))
  
  xml = LoadUrl(url, CACHE_INT_VIDEO_SERIES)
  for episode in xml.xpath(XPATH_VIDEO_SERIES_EP):
    limit = limit - 1
    if limit < 0:
      dir.AppendItem(DirectoryItem(_E(url) + "||" + title, TEXT_ALL_EPISODES, None))
      break
    
    thumb = episode.find("a/img").get("src")
    desc = episode.find("a/img").get("alt")
    epUrl = episode.find("a").get("href")
    dir.AppendItem(CreateVideoItemFromPage(epUrl, thumb, desc))
  
  return dir.ToXML()

def HitList():
  dir = MediaContainer(FILE_DEFAULT_ART, title1=TEXT_IGN, title2=TEXT_HIT_LIST)
  
  count = 0
  for hit in HomePageXml().xpath(XPATH_HIT_LIST):
    count = count + 1
    dir.AppendItem(DirectoryItem(str(count) + "||" + hit.text, hit.text, None))
  
  return dir.ToXML()

def SelectedHit(index, title):
  dir = MediaContainer(FILE_DEFAULT_ART, title1=TEXT_IGN, title2=title)
  
  for video in HomePageXml().xpath(XPATH_SELECTED_HIT % index):
    desc = "" # video.find("p") Why doesn't this return all of the p tags?
    url = video.find("a").get("href")
    thumb = video.find("a/img").get("src")
    title = video.find("h5/a").text
    dir.AppendItem(CreateVideoItemFromPage(url, thumb, desc, title))
  
  return dir.ToXML()

def RecentVideos():
  dir = MediaContainer(FILE_DEFAULT_ART, title1=TEXT_IGN, title2=TEXT_RECENT_VIDEOS)
  
  first = True
  for row in LoadUrl(URL_ALL, CACHE_INT_RECENT).xpath(XPATH_RECENT_VIDEOS):
    if first: # Need to skip header row (Hey IGN, use a thead like the rest of us!)
      first = False
      continue
    
    url = row.find("td//a").get("href")
    name = row.find("td//a").text.strip()
    
    # Need to label category
    icon = row.find("td/img").get("src") # Again, IGN, how about some alt text?
    begin = icon.find("icon_") + 5
    end = icon.find(".gif")
    label = icon[begin:end]
    if label == "video":
      nameLabeled = name
    else:
      nameLabeled = "[" + _L(label) + "] " + name
    
    dir.AppendItem(DirectoryItem(_E(url) + "||" + name, nameLabeled, None))
  
  return dir.ToXML()

def RecentVideosPage(url, title):
  dir = MediaContainer(FILE_DEFAULT_ART, title1=TEXT_IGN, title2=title)
  
  for link in LoadUrl(url, CACHE_INT_RECENT).xpath(XPATH_RECENT_VIDEOS_PAGE):
    url = link.get("href")
    name = link.find("img").get("alt")
    thumb = link.find("img").get("src")
    
    dir.AppendItem(CreateVideoItemFromPage(url, thumb, "", name))
  
  return dir.ToXML()

def HandleRequest(pathNouns, count):
  if count == 0:
    return Index()
  
  if count > 1 and (pathNouns[1] != "all" or count > 2):
    (url, title) = pathNouns[count-1].split("||")
    if pathNouns[0] != PATH_HIT_LIST:
      url = _D(url)
  
  if pathNouns[0] == PATH_TOP_VIDEOS:
    return TopVideos()
  elif pathNouns[0] == PATH_LATEST_VIDEOS:
    return Latest()
  elif pathNouns[0] == PATH_GAME_TRAILERS:
    return GameTrailers()
  elif pathNouns[0] == PATH_MOVIE_TRAILERS:
    return MovieTrailers()
  elif pathNouns[0] == PATH_REVIEWS:
    return Reviews()
  elif pathNouns[0] == PATH_PREVIEWS:
    return Previews()
  elif pathNouns[0] == PATH_VIDEO_SERIES:
    if count == 1:
      return VideoSeries()
    elif pathNouns[1] == "all":
      count = count - 1
    if count == 1:
      return VideoSeries(True)
    elif count == 2:
      return SelectedVideoSeries(url, title, LIMIT_SERIES_EPISODES)
    else:
      return SelectedVideoSeries(url, title)
  elif pathNouns[0] == PATH_HIT_LIST:
    if count == 1:
      return HitList()
    elif count == 2:
      return SelectedHit(url, title)
  elif pathNouns[0] == PATH_RECENT_VIDEOS:
    if count == 1:
      return RecentVideos()
    else:
      return RecentVideosPage(url, title)