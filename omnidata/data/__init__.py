from .abstract import AbstractData, AbstractView, AbstractBuffer

from .buffers import Buffer, RemoteBuffer, HDFBuffer, BufferView, ReplacementBuffer, TransformedBuffer, NarrowBuffer
from .base import DataCollection, DataSource, Dataset, Batch
from .flavors import SimpleDataset, GenerativeDataset, ObservationDataset, \
	SupervisedDataset, LabeledDataset, SyntheticDataset, \
	RootedDataset, EncodableDataset, ImageDataset

from .toy import SwissRollDataset, HelixDataset


# TODO: move to foundation

from .mnist import MNIST, FashionMNIST, KMNIST, EMNIST, SVHN, CIFAR10, CIFAR100
from .disentangling import dSprites, Shapes3D, MPI3D, CelebA