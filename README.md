# Dublabs VCF Files

This repository contains scripts to generate a VCF files to be used by Dublabs. These scripts rely on the Locations API for data. Access to the Locations API is configured here: [https://developer.oregonstate.edu](https://developer.oregonstate.edu)

## Generate a VCF file
Save [configuration.example.json](dublabs/configuration.example.json) as configuration.json and modify as needed. Pass the configuration file as an argument when running [buildings_vcf_generator.py](buildings_vcf_generator.py) or [dining_vcf_generator.py](dining_vcf_generator.py). 

## Dining Location Descriptions
The dining locations use descriptions from [osu-corvallis-food-locations.json](osu-corvallis-food-locations.json). To modify the contents of that file to update the OSU app, modify [osu-corvallis-food-locations.json](osu-corvallis-food-locations.json) as needed and submit a pull request.