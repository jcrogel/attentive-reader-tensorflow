import tensorflow as tf
from tensorflow.models.rnn import rnn, rnn_cell

from base_model import Model
from cells import LSTMCell, MultiRNNCellWithSkipConn
from data_utils import load_vocab, load_dataset

class DeepLSTM(Model):
  """Deep LSTM model."""
  def __init__(self, vocab_size, size=256, depth=3,
               learning_rate=1e-4, batch_size=32,
               keep_prob=0.1, num_steps=100,
               checkpoint_dir="checkpoint", forward_only=False):
    """Initialize the parameters for an Deep LSTM model.
    
    Args:
      vocab_size: int, The dimensionality of the input vocab
      size: int, The dimensionality of the inputs into the Deep LSTM cell [32, 64, 256]
      learning_rate: float, [1e-3, 5e-4, 1e-4, 5e-5]
      batch_size: int, The size of a batch [16, 32]
      keep_prob: unit Tensor or float between 0 and 1 [0.0, 0.1, 0.2]
      num_steps: int, The max time unit [100]
    """
    super(DeepLSTM, self).__init__()

    self.vocab_size = int(vocab_size)
    self.size = int(size)
    self.depth = int(depth)
    self.learning_rate = float(learning_rate)
    self.batch_size = int(batch_size)
    self.keep_prob = float(keep_prob)
    self.num_steps = int(num_steps)

    self.inputs_dict = {}
    for nsteps in xrange(1, self.num_steps):
      self.inputs_dict[nsteps] = tf.placeholder(tf.int32, [self.batch_size, nsteps])

    self.y = tf.placeholder(tf.int32, [self.batch_size])

    with tf.device("/cpu:0"):
      self.emb = tf.get_variable("emb", [vocab_size, size])
      self.embed_inputs_dict = {}
      for nsteps in xrange(1, self.num_steps):
        self.embed_inputs_dict[nsteps] = tf.nn.embedding_lookup(self.emb,
                                                                self.inputs_dict[nsteps])

    self.cell = LSTMCell(size, forget_bias=0.0)
    self.stacked_cell = MultiRNNCellWithSkipConn([self.cell] * depth)

    self.initial_state = self.stacked_cell.zero_state(batch_size, tf.float32)

    if not forward_only and self.keep_prob < 1:
      lstm_cell = rnn_cell.DropoutWrapper(
          lstm_cell, output_keep_prob=keep_prob)

    self.outputs_dict = {}
    for nsteps in xrange(1, self.num_steps):
      _, states = rnn.rnn(self.stacked_cell,
                          tf.unpack(self.embed_inputs_dict[nsteps]),
                          dtype=tf.float32,
                          initial_state=self.initial_state)
      self.outputs_dict[nsteps] = states[-1]

  def train(self, epoch=25, batch_size=1,
            learning_rate=0.0002, momentum=0.9, decay=0.95,
            data_dir="data", dataset_name="cnn", vocab_size=1000000):
    if not self.vocab:
      self.vocab, self.rev_vocab = load_vocab(data_dir, dataset_name, vocab_size)

    with tf.device("/cpu:0"):
      self.W = tf.get_variable("W", [vocab_size, self.size * self.depth])
      W_a = tf.nn.embedding_lookup(W, self._input_data)

    self.opt = tf.train.RMSPropOptimizer(learning_rate,
                                         decay=decay,
                                         momentum=momentum)

    for epoch_idx in xrange(epoch):
      data_loader = load_dataset(data_dir, dataset_name, vocab_size)

      contexts, questions, answers = [], [], []
      for batch_idx in xrange(batch_size):
        _, context, question, answer, _ = data_loader.next()
        contexts.append(context)
        questions.append(question)
        answers.append(answers)

      #self.model.
