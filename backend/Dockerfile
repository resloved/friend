FROM public.ecr.aws/lambda/python:3.8

RUN yum -y install \
    git \
    tar \
    unzip

RUN git clone --recursive https://github.com/saharNooby/rwkv.cpp rwkv
WORKDIR rwkv
RUN curl -L https://github.com/saharNooby/rwkv.cpp/releases/download/master-c736ef5/rwkv-master-c736ef5-bin-Linux-Ubuntu-22.04-x86_64.zip > rwkv-cpp-libary.zip
RUN unzip rwkv-cpp-libary.zip

RUN curl -L https://github.com/resloved/friend/releases/download/friend/friend-3B-Q4-0.tar.gz > friend-3B-Q4-0.tar.gz
RUN tar xvf friend-3B-Q4-0.tar.gz
RUN rm friend-3B-Q4-0.tar.gz
RUN find -name '*.bin' -exec mv {} release.bin \;

COPY app.py ../

ENV PYTHONUNBUFFERED 1

# Set the CMD to your handler
CMD ["app.lambda_handler"]
