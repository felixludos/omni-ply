# from .old_abstract import AbstractData, AbstractView, AbstractBuffer
# from .buffers import Buffer, RemoteBuffer, HDFBuffer, BufferView, ReplacementBuffer, TransformedBuffer, NarrowBuffer
# from .base import DataCollection, DataSource, Dataset, Batch
# from .flavors import SimpleDataset, GenerativeDataset, ObservationDataset, \
# 	SupervisedDataset, LabeledDataset, SyntheticDataset, \
# 	RootedDataset, EncodableDataset, DownloadableDataset, ImageDataset

from .top import Datastream, Buffer, Dataset, Sampledstream
from . import toy
from toy import SwissRollDataset, HelixDataset, SwissRoll, Helix


# TODO: move to foundation

# from omnilearn.datasets.disentangling import dSprites, Shapes3D, MPI3D, CelebA