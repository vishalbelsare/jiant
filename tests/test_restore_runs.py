import os
import os.path
import shutil
import tempfile
import unittest
from unittest import mock

from src import evaluate
import src.tasks.tasks as tasks
from src.utils import utils
from main import evaluate_and_write, get_best_checkpoint_path


class TestCheckpointing(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mrpc = tasks.MRPCTask(self.temp_dir, 100, "mrpc", tokenizer_name="MosesTokenizer")
        self.sst = tasks.MRPCTask(self.temp_dir, 100, "sst", tokenizer_name="MosesTokenizer")
        os.mkdir(os.path.join(self.temp_dir, "mrpc"))
        os.mkdir(os.path.join(self.temp_dir, "sst"))
        for type_name in ["model", "task", "training", "metric"]:
            open(
                os.path.join(self.temp_dir, "{}_state_pretrain_epoch_1.th".format(type_name)), "w"
            ).close()
            open(
                os.path.join(self.temp_dir, "{}_state_pretrain_epoch_2.th".format(type_name)), "w"
            ).close()
            open(
                os.path.join(self.temp_dir, "{}_state_pretrain_epoch_3.best.th".format(type_name)),
                "w",
            ).close()
            open(
                os.path.join(
                    self.temp_dir, "mrpc", "{}_state_target_train_epoch_1.best.th".format(type_name)
                ),
                "w",
            ).close()
            open(
                os.path.join(
                    self.temp_dir, "mrpc", "{}_state_target_train_epoch_2.th".format(type_name)
                ),
                "w",
            ).close()

    def test_check_for_previous_checkpoints(self):
        # Testing that check_for_previous_checkpoints returns the correct checkpoints given
        # the state of a run directory.
        tasks = [self.mrpc, self.sst]
        task_directory, max_epoch, suffix = utils.check_for_previous_checkpoints(
            self.temp_dir, tasks, phase="pretrain", load_model=True
        )
        assert (
            task_directory == "" and max_epoch == 3 and suffix == "state_pretrain_epoch_3.best.th"
        )
        task_directory, max_epoch, suffix = utils.check_for_previous_checkpoints(
            self.temp_dir, tasks, phase="target_train", load_model=True
        )
        assert (
            task_directory == "mrpc"
            and max_epoch == 2
            and suffix == "state_target_train_epoch_2.th"
        )
        # Test partial checkpoints.
        for type_name in ["model", "task"]:
            open(
                os.path.join(
                    self.temp_dir, "sst", "{}_state_target_train_epoch_1.best.th".format(type_name)
                ),
                "w",
            ).close()
        task_directory, max_epoch, suffix = utils.check_for_previous_checkpoints(
            self.temp_dir, tasks, phase="target_train", load_model=True
        )
        assert (
            task_directory == "mrpc"
            and max_epoch == 2
            and suffix == "state_target_train_epoch_2.th"
        )
        for type_name in ["training", "metric"]:
            open(
                os.path.join(
                    self.temp_dir, "sst", "{}_state_target_train_epoch_1.best.th".format(type_name)
                ),
                "w",
            ).close()
            open(
                os.path.join(
                    self.temp_dir, "sst", "{}_state_target_train_epoch_2.best.th".format(type_name)
                ),
                "w",
            ).close()
        task_directory, max_epoch, suffix = utils.check_for_previous_checkpoints(
            self.temp_dir, tasks, phase="target_train", load_model=True
        )
        assert (
            task_directory == "sst"
            and max_epoch == 1
            and suffix == "state_target_train_epoch_1.best.th"
        )

    def test_find_last_checkpoint_epoch(self):
        # Testing path-finding logic of find_last_checkpoint_epoch function.
        max_epoch, suffix = utils.find_last_checkpoint_epoch(
            self.temp_dir, search_phase="pretrain", task_name=""
        )
        assert max_epoch == 3 and suffix == "state_pretrain_epoch_3.best.th"
        max_epoch, suffix = utils.find_last_checkpoint_epoch(
            self.temp_dir, search_phase="target_train", task_name="sst"
        )
        assert max_epoch == -1 and suffix is None
        max_epoch, suffix = utils.find_last_checkpoint_epoch(
            self.temp_dir, search_phase="target_train", task_name="mrpc"
        )
        assert max_epoch == 2 and suffix == "state_target_train_epoch_2.th"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
