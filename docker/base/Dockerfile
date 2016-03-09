FROM centos:7

MAINTAINER Naftuli Tzvi Kay <rfkrocktk@gmail.com>

# environment variables set at the top to make bumping revisions for security updates easy
ENV IMAGE_RELEASE=1
ENV LANG=en_US.UTF-8
ENV POWERPY_USER=powerpy
ENV POWERPY_UID=8080

# upgrade everything for security updates
RUN yum upgrade -y >/dev/null

# install python and dependencies
RUN yum install -y python-devel gcc gcc-c++ make openssl-devel ImageMagick unoconv python-pip >/dev/null

# create powerpy user
RUN useradd -r -u $POWERPY_UID $POWERPY_USER

# create and add sources
RUN mkdir -p -m 0755 /srv/powerpy
ADD bootstrap-buildout.py buildout.cfg setup.py /srv/powerpy/
ADD src/ /srv/powerpy/src/
RUN chown -R $POWERPY_USER:$POWERPY_USER /srv/powerpy

# run all commands from here as $POWERPY_USER in /srv/powerpy/
USER $POWERPY_USER
WORKDIR /srv/powerpy/

# bootstrap the buildout
RUN python bootstrap-buildout.py > /dev/null

# run the buildout
RUN bin/buildout
