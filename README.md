# Steam Scraper

This repository contains [Scrapy](https://github.com/scrapy/scrapy) spiders for **crawling games** and **scraping all user-submitted reviews** from the [Steam game store](https://steampowered.com).


## Installation

After cloning the repository with
```bash
git clone git@github.com:prncc/steam-scraper.git
```
start and activate a Python 3.6+ virtualenv with
```bash
cd steam-scraper
virtualenv -p python3.6 env
. env/bin/activate
```
Install Python requirements via:
```bash
pip install -r requirements.txt
```


## Crawling the Products

The purpose of `ProductSpider` is to discover product pages on the [Steam product listing](http://store.steampowered.com/search/?sort_by=Released_DESC) and extract useful metadata from them.
A neat feature of this spider is that it automatically navigates through Steam's age verification checkpoints.
You can initiate the multi-hour crawl with
```bash
scrapy crawl products -o output/products_all.jl --logfile=output/products_all.log --loglevel=INFO -s JOBDIR=output/products_all_job -s HTTPCACHE_ENABLED=False
```
When it completes you should have metadata for all games on Steam in `output/products_all.jl`.
Here's some example output:
```python
{
  'app_name': 'Cold Fear™',
  'developer': 'Darkworks',
  'early_access': False,
  'genres': ['Action'],
  'id': '15270',
  'metascore': 66,
  'n_reviews': 172,
  'price': 9.99,
  'publisher': 'Ubisoft',
  'release_date': '2005-03-28',
  'reviews_url': 'http://steamcommunity.com/app/15270/reviews/?browsefilter=mostrecent&p=1',
  'sentiment': 'Very Positive',
  'specs': ['Single-player'],
  'tags': ['Horror', 'Action', 'Survival Horror', 'Zombies', 'Third Person', 'Third-Person Shooter'],
  'title': 'Cold Fear™',
  'url': 'http://store.steampowered.com/app/15270/Cold_Fear/'
 }
```

## Extracting the Reviews

The purpose of `ReviewSpider` is to scrape all user-submitted reviews of a particular product from the [Steam community portal](http://steamcommunity.com/). 
By default, it starts from URLs listed in its `test_urls` parameter:
```python

class ReviewSpider(scrapy.Spider):
    name = 'reviews'
    test_urls = [
        "https://steamcommunity.com/app/1501750/reviews/?browsefilter=toprated&snr=1_5_100010_", 
        "https://steamcommunity.com/app/2195250/reviews/?browsefilter=toprated&snr=1_5_100010_",
        "https://steamcommunity.com/app/289070/reviews/?browsefilter=toprated&snr=1_5_100010_"]
```
It can alternatively ingest a text file containing URLs such as

```
http://steamcommunity.com/app/316790/reviews/?browsefilter=mostrecent&p=1
http://steamcommunity.com/app/207610/reviews/?browsefilter=mostrecent&p=1
http://steamcommunity.com/app/414700/reviews/?browsefilter=mostrecent&p=1
```
via the `url_file` command line argument:
```bash
scrapy crawl reviews -o reviews.jl -a url_file=url_file.txt -s JOBDIR=output/reviews
```
An output sample:

```python

{'app_name': 'THE DREADFUL SPACE',
 'developer': 'Caztellary Studio',
 'early_access': False,
 'genre': ['Action', 'Adventure', 'Casual', 'Indie'],
 'id': '1944000',
 'price': '3.00 AED',
 'publisher': 'Caztellary Studio',
 'release_date': '30 Apr, 2022',
 'reviews_url': 'http://steamcommunity.com/app/1944000/reviews/?browsefilter=mostrecent&p=1',
 'sentiment': 'Positive',
 'tags': ['Indie',
          'Action',
          'Spaceships',
          'Arcade',
          'Adventure',
          'Shooter',
          'Wargame',
          'Aliens',
          'Action-Adventure',
          'War',
          'Bullet Hell',
          'Collectathon',
          "Shoot 'Em Up",
          'Arena Shooter',
          'Flight',
          'Colorful',
          'Minimalist',
          'Combat',
          'Controller',
          'PvE'],
 'title': 'THE DREADFUL SPACE',
 'url': 'https://store.steampowered.com/app/1944000/THE_DREADFUL_SPACE/'}

```

If you want to get all the reviews for all the games, `split_review_urls.py` will remove duplicate entries from `products_all.jl` and shuffle `review_url`s into several text files.
This provides a convenient way to split up your crawl into manageable pieces.
The whole job takes a few days with Steam's generous rate limits.

## Deploying to a Remote Server

This section briefly explains how to run the crawl on one or more t1.micro AWS instances.

First, create an Ubuntu 16.04 t1.micro instance and name it `scrapy-runner-01` in your `~/.ssh/config` file:
```
Host scrapy-runner-01
     User ubuntu
     HostName <server's IP>
     IdentityFile ~/.ssh/id_rsa
```
A hostname of this form is expected by the `scrapydee.sh` helper script included in this repository.
Make sure you can connect with `ssh scrappy-runner-01`.

### Remote Server Setup

The tool that will actually run the crawl is [scrapyd](http://scrapyd.readthedocs.io/en/stable/) running on the remote server.
To set things up first install Python 3.10:
```bash
sudo add-apt-repository ppa:jonathonf/python-3.10
sudo apt update
sudo apt install python3.10 python3.10-dev virtualenv python-pip
```
Then, install scrapyd and the remaining requirements in a dedicated `run` directory on the remote server: 
```bash
mkdir run && cd run
virtualenv -p python3.10 env
. env/bin/activate
pip install scrapy scrapyd botocore smart_getenv  
```
You can run `scrapyd` from the virtual environment with
```bash
scrapyd --logfile /home/ubuntu/run/scrapyd.log &
```
You may wish to use something like [screen](https://www.gnu.org/software/screen/) to keep the process alive if you disconnect from the server.

### Controlling the Job

You can issue commands to the scrapyd process running on the remote machine using a simple [HTTP JSON API](http://scrapyd.readthedocs.io/en/stable/index.html).
First, create an egg for this project:
```bash
python setup.py bdist_egg
```
Copy the egg and your review url file to `scrapy-runner-01` via
```bash
scp output/review_urls_01.txt scrapy-runner-01:/home/ubuntu/run/
scp dist/steam_scraper-1.0-py3.10.egg scrapy-runner-01:/home/ubuntu/run
```
and add it to scrapyd's job directory via 
```bash
ssh -f scrapy-runner-01 'cd /home/ubuntu/run && curl http://localhost:6800/addversion.json -F project=steam -F egg=@steam_scraper-1.0-py3.`0`.egg'
```
Opening port 6800 to TCP traffic coming from your home IP would allow you to issue this command without going through SSH.
If this command doesn't work, you may need to edit `scrapyd.conf` to contain
```
bind_address = 0.0.0.0
```
in the `[scrapyd]` section.
This is a good time to mention that there exists a [scrapyd-client](https://github.com/scrapy/scrapyd-client) project for deploying eggs to scrapyd equipped servers.
I chose not to use it because it doesn't know about servers already set up in `~/.ssh/config` and so requires repetitive configuration.

### Running the scraper on an AWS EC2 instance
If you want to run your Scrapy spider on AWS (Amazon Web Services) and save the output to a CSV file, you can use AWS services such as EC2 (Elastic Compute Cloud) for hosting your spider and S3 (Simple Storage Service) for storing the output data. Here's a general guide:

#### Steps:
1. Create an EC2 Instance:

2. Launch an EC2 instance on AWS. You can choose an Amazon Machine Image (AMI) with a suitable environment for your Scrapy project (e.g., an Amazon Linux image).
Connect to the EC2 Instance:

3. Connect to your EC2 instance using SSH. You'll need the public IP address or DNS of your instance and the private key associated with the key pair used when launching the instance.
Install Dependencies on EC2:

4. On the EC2 instance, install Python, Scrapy, and any other dependencies required for your Scrapy project.
Copy Your Scrapy Project to EC2:

5. Copy your Scrapy project files to the EC2 instance. You can use scp (secure copy) to transfer files from your local machine to the EC2 instance.

Example:

```bash 
scp -i /path/to/your/private-key.pem -r /path/to/your/scrapy-project ec2-user@your-ec2-ip:/path/on/ec2
```
Configure Scrapy Settings:

Modify your Scrapy project's settings to use AWS S3 as the output location. Set the FEED_URI to an S3 path, and provide your AWS credentials.

Example:

```python
settings.py
FEEDS = {
    's3://your-bucket-name/output.csv': {
        'format': 'csv',
        'overwrite': True,
    },
}
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
```
Run Your Scrapy Spider:

Run your Scrapy spider on the EC2 instance. You can use a tool like tmux to keep the process running even if you disconnect from the instance.
Access the Output on S3:

Once the spider completes, the CSV output will be stored in the specified S3 bucket. You can access it using the AWS S3 console or download it programmatically.
Notes:
Ensure that your EC2 instance has the necessary permissions to write to the specified S3 bucket.
You may need to configure the security group of your EC2 instance to allow outbound internet access for downloading dependencies.
Always be mindful of AWS costs associated with EC2 instances, S3 storage, and data transfer.

#### Using Docker? 
To run a Docker container on an EC2 instance, you need to follow these general steps. Please note that these steps assume you've already set up Docker on your EC2 instance.

1. Connect to Your EC2 Instance:
Use SSH to connect to your EC2 instance. Replace your-ec2-instance-ip with the actual IP address or DNS of your EC2 instance:
```bash
ssh -i your-key.pem ec2-user@your-ec2-instance-ip
```

2. Copy Your Dockerfile and Code:
Transfer your Dockerfile and the necessary code to your EC2 instance. You can use scp for this:
```bash
scp -i your-key.pem -r /path/to/your/code ec2-user@your-ec2-instance-ip:/path/to/destination
```
3. Connect to your EC2 instance again to navigate to the directory where you copied your Dockerfile and code.

4. Build the Docker Image:
Build your Docker image using the Dockerfile:

```bash
docker build -t your-image-name .
```
5. Run the Docker Container:
Run the Docker container based on the image you built:

```bash
docker run -d your-image-name
```
The -d flag runs the container in detached mode.

6. Check Running Containers:
Check if your container is running:

```bash
docker ps
```
This command will display a list of running containers.


Now, your Docker container should be running on your EC2 instance. Keep in mind that you might need to expose and publish ports if your application inside the container requires external access.

If your application involves web scraping and you're using Scrapyd, ensure that Scrapyd is properly configured and running. Also, consider whether you want to expose the Scrapyd web service port if you plan to interact with Scrapyd through its API.

### Output Format

 If you are running both the games and reviews spider and you want to store their outputs in separate CSV files, you can modify the `FEED_URI` setting dynamically based on the spider's name in the` settings.py` file. It automatically stores the output as the default spider names (i.e. GamesSpider.csv and ReviewSpider.csv)
