# Blue Button Web Server

[![Build Status](https://travis-ci.org/CMSgov/bluebutton-web-server.svg?branch=develop)](https://travis-ci.org/CMSGov/hhs_oauth_server)
[![Coverage Status](https://coveralls.io/repos/github/CMSgov/bluebutton-web-server/badge.svg?branch=develop)](https://coveralls.io/github/CMSgov/bluebutton-web-server?branch=develop)

This server serves as a data provider for sharing Medicare claims data with third parties.
The server connects to Medicare.gov for authentication, and uses OAuth2 to confirm permission
grants to external app developers. The data itself comes from a back end FHIR server
(https://github.com/CMSgov/bluebutton-data-server), which in turn pulls data from the CMS
Chronic Conditions Warehouse (https://www.ccwdata.org)

## About the Project

**This server serves as a data provider for sharing Medicare claims data with third parties. The server connects to Medicare.gov for authentication, and uses OAuth2 to confirm permission grants to external app developers.**

For more information on how to connect to the API implemented here, check out our developer documentation at https://cmsgov.github.io/bluebutton-developer-help/. Our most recent deployment is at https://sandbox.bluebutton.cms.gov, and you can also check out our Google Group at https://groups.google.com/forum/#!forum/developer-group-for-cms-blue-button-api for more details.

The information below outlines setting up the server for development or your own environment. For general information on deploying Django see https://docs.djangoproject.com/en/4.2/howto/deployment/.

NOTE: Internal software engineers or other interested parties should follow the documentation for running a Dockerized local development enviornment. For more information see https://github.com/CMSgov/bluebutton-web-server/blob/master/docker-compose/readme.md.

### Agency Mission

The Centers for Medicare & Medicaid Services (CMS) is working to enable Medicare beneficiaries to securely share their health data with applications of their choice through standards-based APIs.

### Core Team

A list of core team members responsible for the code and documentation in this repository can be found in [COMMUNITY.md](COMMUNITY.md).

## Community

The Blue Button Web Server team is taking a community-first and open source approach to the product development of this tool. We believe government software should be made in the open and be built and licensed such that anyone can download the code, run it themselves without paying money to third parties or using proprietary software, and use it as they will.

We know that we can learn from a wide variety of communities, including those who will use or will be impacted by the tool, who are experts in technology, or who have experience with similar technologies deployed in other spaces. We are dedicated to creating forums for continuous conversation and feedback to help shape the design and development of the tool.

We also recognize capacity building as a key part of involving a diverse open source community. We are doing our best to use accessible language, provide technical and process documents, and offer support to community members with a wide variety of backgrounds and skillsets.

### Community Guidelines

Principles and guidelines for participating in our open source community are can be found in [COMMUNITY.md](COMMUNITY.md). Please read them before joining or starting a conversation in this repo or one of the channels listed below. All community members and participants are expected to adhere to the community guidelines and code of conduct when participating in community spaces including: code repositories, communication channels and venues, and events.

### Contributing

Thank you for considering contributing to an Open Source project of the US Government! For more information about our contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Feedback

If you have ideas for how we can improve or add to our capacity building efforts and methods for welcoming people into our community, please let us know at **opensource@cms.hhs.gov**. If you would like to comment on the tool itself, please let us know by filing an **issue on our GitHub repository.**

## Policies

This project is free and open source software under the Apache2 license. You may add additional applications, authentication backends, and styles/themes are not subject to the Apache2 license.

In other words, you or your organization are not in any way prevented from build closed source applications on top of this tool. Applications that you create can be licensed in any way that suits you business or organizational needs. Any 3rd party applications are subject to the license in which they are distributed by their respective authors.

### Open Source Policy

We adhere to the [CMS Open Source Policy](https://github.com/CMSGov/cms-open-source-policy). If you have any questions, just [shoot us an email](mailto:opensource@cms.hhs.gov).

### Security and Responsible Disclosure Policy

_Submit a vulnerability:_ Vulnerability reports can be submitted through [Bugcrowd](https://bugcrowd.com/cms-vdp). Reports may be submitted anonymously. If you share contact information, we will acknowledge receipt of your report within 3 business days.

For more information about our Security, Vulnerability, and Responsible Disclosure Policies, see [SECURITY.md](SECURITY.md).

### Software Bill of Materials (SBOM)

A Software Bill of Materials (SBOM) is a formal record containing the details and supply chain relationships of various components used in building software.

In the spirit of [Executive Order 14028 - Improving the Nation's Cyber Security](https://www.gsa.gov/technology/it-contract-vehicles-and-purchasing-programs/information-technology-category/it-security/executive-order-14028), a SBOM for this repository is provided here: https://github.com/CMSGov/bluebutton-web-server/network/dependencies.

For more information and resources about SBOMs, visit: https://www.cisa.gov/sbom.

## License

Licensed under the Apache License, Version 2.0 (the "License"); 
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
