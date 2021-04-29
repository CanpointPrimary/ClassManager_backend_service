FROM redis

COPY run-sentinel.sh /run-sentinel.sh

COPY sentinel.conf /etc/sentinel.conf

RUN chmod +x /run-sentinel.sh

ENTRYPOINT ["/run-sentinel.sh"]