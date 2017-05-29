from flask_restful import (
    Resource,
    abort,
)
import inspect

from ...resources import recorder


# recorder data
RECORDERS = {
    obj.NAME: {'name': name, 'obj': obj} for name, obj in inspect.getmembers(recorder) if inspect.isclass(obj)
}


def abort_if_recorder_doesnt_exist(recorder_name):
    if recorder_name not in RECORDERS:
        abort(404, message="Recorder {} doesn't exist".format(recorder_name))


class RecorderList(Resource):

    def get(self):
        return {
            obj.NAME: {'name': name} for name, obj in inspect.getmembers(recorder) if inspect.isclass(obj)
        }


class Recorder(Resource):

    def get(self, recorder_name):
        abort_if_recorder_doesnt_exist(recorder_name)
        return RECORDERS[recorder_name]