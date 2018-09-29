Web Counter
===========

## Description

This program is a traditional hit counter.

## Deploy

```bash
$ docker build -t counter .
$ docker run -e "TZ=Asia/Tokyo" -p 8000:8000 -d --rm -it counter
$ curl localhost:8000/json
{"count":1}
$ curl localhost:8000/html
<!DOCTYPE html><html><head> ... </div></body></html>
```

## How to use

1. Deploy and run this program on a web server.
2. Add html embed code to your website.
 
```html
<iframe src="http://[server]:[port]/html" width="150" height="20" frameborder="0">
```

## Options

All options are provided with environment variables.

- TZ  
  timezone (default: "UTC")
- IMAGE_WIDTH  
  image width (only html mode)
- IMAGE_HEIGHT  
  image height (only html mode)
- MIN_DIGITS   
  the number of digits (only html mode)

## License
[MIT License](https://opensource.org/licenses/MIT)

## Author
markdevel (markdevel [AT] outlook [.] com)
