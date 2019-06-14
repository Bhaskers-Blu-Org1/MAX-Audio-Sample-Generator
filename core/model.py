#
# Copyright 2018-2019 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from maxfw.model import MAXModelWrapper
import tensorflow as tf
import numpy as np
import logging
from config import DEFAULT_MODEL_PATH, MODELS, INPUT_TENSOR, OUTPUT_TENSOR, MODEL_META_DATA as model_meta
import scipy.io.wavfile

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class SingleModelWrapper(object):

    def __init__(self, model, path):
        self.graph = tf.Graph()
        with self.graph.as_default():
            self.sess = tf.Session(graph=self.graph)
            saver = tf.train.import_meta_graph('{}/train_{}/infer/infer.meta'.format(path, model))
            saver.restore(self.sess, tf.train.latest_checkpoint('{}/train_{}/'.format(path, model)))
            self.input = self.graph.get_tensor_by_name(INPUT_TENSOR)
            self.output = self.graph.get_tensor_by_name(OUTPUT_TENSOR)

    def predict(self):
        # Create 50 random latent vectors z
        _z = (np.random.rand(50, 100) * 2.) - 1
        # Synthesize G(input)
        preds = self.sess.run(self.output, {self.input: _z})
        return preds


class ModelWrapper(MAXModelWrapper):

    MODEL_META_DATA = model_meta

    def __init__(self, path=DEFAULT_MODEL_PATH):
        logger.info('Loading models from: {}...'.format(path))
        self.models = {}
        for model in MODELS:
            logger.info('Loading model: {}'.format(model))
            self.models[model] = SingleModelWrapper(model=model, path=path)

        logger.info('Loaded all models')

    def _predict(self, model):
        logger.info('Generating audio from model: {}'.format(model))
        preds = self.models[model].predict()

        # convert audio to 16 bit so that it can play in firefox
        audio_data = np.round(preds[0] * np.iinfo(np.int16).max)
        audio_data = audio_data.astype(np.int16)

        scipy.io.wavfile.write("output.wav", 16000, audio_data)
        wav_bytes = open('output.wav')
        return wav_bytes
