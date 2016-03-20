#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# author: jiehua233@gmail.com
#

import falcon
import redis
import ujson as json
import config
from wsgiref import simple_server


def validate_direction(req, resp, resource, params):
    direction = params.get("direction")
    if direction == "positive":
        params["direction"] = 0
    elif direction == "negative":
        params["direction"] = 1
    else:
        raise falcon.HTTPBadRequest("Error", "Illegal direction")


class BusResource(object):

    def __init__(self):
        rpool = redis.ConnectionPool(**config.REDIS)
        self.rds = redis.StrictRedis(connection_pool=rpool)

    @falcon.before(validate_direction)
    def on_get(self, req, resp, direction):
        resp.status = falcon.HTTP_200
        result = {"c": 0, "d": {}, "msg": ""}
        data = self.rds.get(config.REDISKEY)
        if data:
            bus_data = json.loads(data)
            result["d"] = self.pack_data(direction, bus_data["content"])
            result["msg"] = "Success"
        else:
            result["c"] = -1
            result["msg"] = "No bus data"

        resp.body = json.dumps(result)

    def pack_data(self, direction, bus):
        d = bus[direction]
        result = {
            "busLine": {
                "lineName": d['busLine']['lineName'],
                "firstTime": d['busLine']['firstTime'],
                "lastTime": d['busLine']['lastTime'],
                "strPlatName": d['busLine']['strPlatName'],
                "endPlatName": d['busLine']['endPlatName'],
                "totalPlat": d['busLine']['totalPlat'],
                "stationNames": d['busLine']['stationNames'],
                "flagSubway": d['busLine']['flagSubway'],
            },
            "busTerminal": [],
        }
        for b in d["busTerminal"]:
            result["busTerminal"].append({
                "stationSeq": b["stationSeq"],
                "adflag": b["adflag"],
            })

        return result


app = falcon.API()
bus = BusResource()
app.add_route("/{direction}", bus)


if __name__ == "__main__":
    host_port = config.bind.split(":")
    httpd = simple_server.make_server(host_port[0], int(host_port[1]), app)
    httpd.serve_forever()
