"""
BDD100K Dataset Loader
"""
import logging
import json
import os
import numpy as np
from PIL import Image

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import torch
import torchvision.transforms as transforms
from src.datamodules.seg import uniform
from src.datamodules.seg import cityscapes_labels
from src.datamodules.seg.base_dataset import BaseDataset

trainid_to_name = cityscapes_labels.trainId2name
id_to_trainid = cityscapes_labels.label2trainid
trainid_to_trainid = cityscapes_labels.trainId2trainId
color_to_trainid = cityscapes_labels.color2trainId
num_classes = 19
ignore_label = 255
img_postfix = '.jpg'

palette = [128, 64, 128, 244, 35, 232, 70, 70, 70, 102, 102, 156, 190, 153, 153,
           153, 153, 153, 250, 170, 30,
           220, 220, 0, 107, 142, 35, 152, 251, 152, 70, 130, 180, 220, 20, 60,
           255, 0, 0, 0, 0, 142, 0, 0, 70,
           0, 60, 100, 0, 80, 100, 0, 0, 230, 119, 11, 32]
zero_pad = 256 * 3 - len(palette)
for i in range(zero_pad):
    palette.append(0)

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

cfg = dotdict({})
cfg.DATASET = dotdict({})
cfg.DATASET.CV_SPLITS = 3


# def colorize_mask(mask):
#     """
#     Colorize a segmentation mask.
#     """
#     # mask: numpy array of the mask
#     new_mask = Image.fromarray(mask.astype(np.uint8)).convert('P')
#     new_mask.putpalette(palette)
#     return new_mask


def add_items(items, aug_items, img_path, mask_path, mask_postfix, mode, maxSkip):
    """

    Add More items ot the list from the augmented dataset
    """

    if mode == "train":
        img_path = os.path.join(img_path, 'train')
        mask_path = os.path.join(mask_path, 'train')
    elif mode == "val":
        img_path = os.path.join(img_path, 'val')
        mask_path = os.path.join(mask_path, 'val')
    elif mode == "small":
        img_path = os.path.join(img_path, 'small')
        mask_path = os.path.join(mask_path, 'small')
    else: 
        raise ValueError("Invalid mode")

    list_items = [name.split(img_postfix)[0] for name in
                os.listdir(img_path)]
    for it in list_items:
        item = (os.path.join(img_path, it + img_postfix),
                os.path.join(mask_path, it + mask_postfix))
        # ########################################################
        # ###### dataset augmentation ############################
        # ########################################################
        # if mode == "train" and maxSkip > 0:
        #     new_img_path = os.path.join(aug_root, 'leftImg8bit_trainvaltest', 'leftImg8bit')
        #     new_mask_path = os.path.join(aug_root, 'gtFine_trainvaltest', 'gtFine')
        #     file_info = it.split("_")
        #     cur_seq_id = file_info[-1]

        #     prev_seq_id = "%06d" % (int(cur_seq_id) - maxSkip)
        #     next_seq_id = "%06d" % (int(cur_seq_id) + maxSkip)
        #     prev_it = file_info[0] + "_" + file_info[1] + "_" + prev_seq_id
        #     next_it = file_info[0] + "_" + file_info[1] + "_" + next_seq_id
        #     prev_item = (os.path.join(new_img_path, c, prev_it + img_postfix),
        #                  os.path.join(new_mask_path, c, prev_it + mask_postfix))
        #     if os.path.isfile(prev_item[0]) and os.path.isfile(prev_item[1]):
        #         aug_items.append(prev_item)
        #     next_item = (os.path.join(new_img_path, c, next_it + img_postfix),
        #                  os.path.join(new_mask_path, c, next_it + mask_postfix))
        #     if os.path.isfile(next_item[0]) and os.path.isfile(next_item[1]):
        #         aug_items.append(next_item)
        items.append(item)
    # items.extend(extra_items)


# def make_cv_splits(img_dir_name):
#     """
#     Create splits of train/val data.
#     A split is a lists of cities.
#     split0 is aligned with the default Cityscapes train/val.
#     """
#     trn_path = os.path.join(root, img_dir_name, 'train')
#     val_path = os.path.join(root, img_dir_name, 'val')

#     trn_cities = ['train/' + c for c in os.listdir(trn_path)]
#     val_cities = ['val/' + c for c in os.listdir(val_path)]

#     # want reproducible randomly shuffled
#     trn_cities = sorted(trn_cities)

#     all_cities = val_cities + trn_cities
#     num_val_cities = len(val_cities)
#     num_cities = len(all_cities)

#     cv_splits = []
#     for split_idx in range(cfg.DATASET.CV_SPLITS):
#         split = {}
#         split['train'] = []
#         split['val'] = []
#         offset = split_idx * num_cities // cfg.DATASET.CV_SPLITS
#         for j in range(num_cities):
#             if j >= offset and j < (offset + num_val_cities):
#                 split['val'].append(all_cities[j])
#             else:
#                 split['train'].append(all_cities[j])
#         cv_splits.append(split)

#     return cv_splits


# def make_split_coarse(img_path):
#     """
#     Create a train/val split for coarse
#     return: city split in train
#     """
#     all_cities = os.listdir(img_path)
#     all_cities = sorted(all_cities)  # needs to always be the same
#     val_cities = []  # Can manually set cities to not be included into train split

#     split = {}
#     split['val'] = val_cities
#     split['train'] = [c for c in all_cities if c not in val_cities]
#     return split


# def make_test_split(img_dir_name):
#     test_path = os.path.join(root, img_dir_name, 'leftImg8bit', 'test')
#     test_cities = ['test/' + c for c in os.listdir(test_path)]

#     return test_cities


def make_dataset(root, mode_input, maxSkip=0, cv_split=0):
    """
    Assemble list of images + mask files

    fine -   modes: train/val/test/trainval    cv:0,1,2
    coarse - modes: train/val                  cv:na

    path examples:
    leftImg8bit_trainextra/leftImg8bit/train_extra/augsburg
    gtCoarse/gtCoarse/train_extra/augsburg
    """
    items = []
    aug_items = []
    
    if len(mode_input.split("_")) == 1:
        mode = mode_input
        sample = None
    else:
        mode, sample = mode_input.split("_")
        sample = int(sample)

    assert mode in ['train', 'val', 'test', 'trainval', 'small']
    img_path = os.path.join(root, 'images/10k') # TODO
    mask_path = os.path.join(root, 'labels/sem_seg/masks')
    mask_postfix = '_train_id.png'
    # mask_postfix = '.png'
    # cv_splits = make_cv_splits(img_dir_name)
    if mode == 'trainval':
        modes = ['train', 'val']
    else:
        modes = [mode]
        
    for mode in modes:
        logging.info('{} fine cities: '.format(mode))
        add_items(items, aug_items, img_path, mask_path,
                    mask_postfix, mode, maxSkip)
    
    logging.info('BDD100K-{}: {} images'.format(mode, len(items) + len(aug_items)))
    if sample is not None:
        import random
        random.shuffle(items)
        items = items[:sample]
        logging.info('BDD100K-{}: sampled {} images'.format(mode, len(items)))
    return items, aug_items


class BDD100KDataSet(BaseDataset):

    def __init__(self, root, mode, maxSkip=0, joint_transform=None, sliding_crop=None, crop_size=None,
                 transform=None, target_transform=None, target_aux_transform=None, dump_images=False,
                 cv_split=None, eval_mode=False, mean=None,
                 eval_scales=None, eval_flip=False, image_in=False,
                 extract_feature=False):
        self.mode = mode
        self.maxSkip = maxSkip
        self.joint_transform = joint_transform
        self.sliding_crop = sliding_crop
        self.transform = transform
        self.target_transform = target_transform
        self.target_aux_transform = target_aux_transform
        self.dump_images = dump_images
        self.eval_mode = eval_mode
        self.eval_flip = eval_flip
        self.eval_scales = None
        self.image_in = image_in
        self.extract_feature = extract_feature
        self.image_size = crop_size
        self.labels_size = crop_size
        if eval_scales != None:
            self.eval_scales = [float(scale) for scale in eval_scales.split(",")]

        if cv_split:
            self.cv_split = cv_split
            assert cv_split < cfg.DATASET.CV_SPLITS, \
                'expected cv_split {} to be < CV_SPLITS {}'.format(
                    cv_split, cfg.DATASET.CV_SPLITS)
        else:
            self.cv_split = 0
        self.imgs, _ = make_dataset(root, mode, self.maxSkip, cv_split=self.cv_split)
        if len(self.imgs) == 0:
            raise RuntimeError('Found 0 images, please check the data set')
        self.mean = mean
        self.mean_std = ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])

    def _eval_get_item(self, img, mask, scales, flip_bool):
        return_imgs = []
        if scales is None: scales = [1.0]
        for flip in range(int(flip_bool) + 1):
            imgs = []
            if flip:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            for scale in scales:
                w, h = img.size
                target_w, target_h = int(w * scale), int(h * scale)
                resize_img = img.resize((target_w, target_h))
                tensor_img = transforms.ToTensor()(resize_img)
                final_tensor = transforms.Normalize(*self.mean_std)(tensor_img)
                imgs.append(final_tensor)
            return_imgs.append(imgs)
        return_imgs.append(img)
        return return_imgs, mask

    def __getitem__(self, index):
        # manually load image and mask
        img_path, mask_path = self.imgs[index]
        img, mask = Image.open(img_path).convert('RGB'), Image.open(mask_path)
        img_name = os.path.splitext(os.path.basename(img_path))[0]

        # Get original dimensions
        w, h = img.size
        
        # Ensure landscape orientation (width > height)
        if h > w:
            img = img.transpose(Image.ROTATE_90)
            mask = mask.transpose(Image.ROTATE_90)
            w, h = h, w  # Swap dimensions
        
        # Calculate target dimensions maintaining aspect ratio
        target_w = 1280  # Fixed width
        target_h = int(h * (target_w / w))
        
        # Ensure height is divisible by 32
        target_h = (target_h // 32) * 32
        
        # Resize both image and mask to target dimensions
        img = img.resize((target_w, target_h), Image.BICUBIC)
        mask = mask.resize((target_w, target_h), Image.NEAREST)
        
        # Convert mask to numpy array and process labels
        mask = np.array(mask)
        mask_copy = mask.copy()
        for k, v in trainid_to_trainid.items():
            mask_copy[mask == k] = v

        # Convert image to numpy array and normalize
        img = np.array(img)
        if self.mean is not None:
            img = img - self.mean

        if self.eval_mode:
            # Convert to tensor and normalize
            img = torch.from_numpy(img).float().permute(2, 0, 1)
            mask_copy = torch.from_numpy(mask_copy).int().squeeze()
            return img, mask_copy, "", img_name
        
        # Convert mask back to PIL Image for transforms
        mask = Image.fromarray(mask_copy.astype(np.uint8))

        # Image Transformations
        if self.extract_feature is not True:
            if self.joint_transform is not None:
                img, mask = self.joint_transform(img, mask)

        if self.transform is not None:
            img = self.transform(img)
        img = img * 255

        rgb_mean_std_gt = ([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
        img_gt = transforms.Normalize(*rgb_mean_std_gt)(img)

        rgb_mean_std = ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        if self.image_in:
            eps = 1e-5
            rgb_mean_std = ([torch.mean(img[0]), torch.mean(img[1]), torch.mean(img[2])],
                    [torch.std(img[0])+eps, torch.std(img[1])+eps, torch.std(img[2])+eps])
        img = transforms.Normalize(*rgb_mean_std)(img)

        if self.target_aux_transform is not None:
            mask_aux = self.target_aux_transform(mask)
        else:
            mask_aux = torch.tensor([0])
        if self.target_transform is not None:
            mask = self.target_transform(mask)

        # Debug
        if self.dump_images:
            outdir = '../../dump_imgs_{}'.format(self.mode)
            os.makedirs(outdir, exist_ok=True)
            out_img_fn = os.path.join(outdir, img_name + '.png')
            out_msk_fn = os.path.join(outdir, img_name + '_mask.png')
            mask_img = colorize_mask(np.array(mask))
            img.save(out_img_fn)
            mask_img.save(out_msk_fn)
        
        return img, mask, img_name, mask_aux

    def __len__(self):
        return len(self.imgs)

class BDD100KDataSetUniform(BaseDataset):
    """
    Please do not use this for AGG
    """

    def __init__(self, mode, maxSkip=0, joint_transform_list=None, sliding_crop=None,
                 transform=None, target_transform=None, target_aux_transform=None, dump_images=False,
                 cv_split=None, class_uniform_pct=0.5, class_uniform_tile=1024,
                 test=False, coarse_boost_classes=None, image_in=False, extract_feature=False):
        self.mode = mode
        self.maxSkip = maxSkip
        self.joint_transform_list = joint_transform_list
        self.sliding_crop = sliding_crop
        self.transform = transform
        self.target_transform = target_transform
        self.target_aux_transform = target_aux_transform
        self.dump_images = dump_images
        self.class_uniform_pct = class_uniform_pct
        self.class_uniform_tile = class_uniform_tile
        self.coarse_boost_classes = coarse_boost_classes
        self.image_in = image_in
        self.extract_feature = extract_feature


        if cv_split:
            self.cv_split = cv_split
            assert cv_split < cfg.DATASET.CV_SPLITS, \
                'expected cv_split {} to be < CV_SPLITS {}'.format(
                    cv_split, cfg.DATASET.CV_SPLITS)
        else:
            self.cv_split = 0

        self.imgs, self.aug_imgs = make_dataset(mode, self.maxSkip, cv_split=self.cv_split)
        assert len(self.imgs), 'Found 0 images, please check the data set'

        # Centroids for fine data
        json_fn = 'bdd100k_{}_cv{}_tile{}.json'.format(
            self.mode, self.cv_split, self.class_uniform_tile)
        if os.path.isfile(json_fn):
            with open(json_fn, 'r') as json_data:
                centroids = json.load(json_data)
            self.centroids = {int(idx): centroids[idx] for idx in centroids}
        else:
            self.centroids = uniform.class_centroids_all(
                self.imgs,
                num_classes,
                id2trainid=trainid_to_trainid,
                tile_size=class_uniform_tile)
            with open(json_fn, 'w') as outfile:
                json.dump(self.centroids, outfile, indent=4)

        self.fine_centroids = self.centroids.copy()

        self.build_epoch()

    def cities_uniform(self, imgs, name):
        """ list out cities in imgs_uniform """
        cities = {}
        for item in imgs:
            img_fn = item[0]
            img_fn = os.path.basename(img_fn)
            city = img_fn.split('_')[0]
            cities[city] = 1
        city_names = cities.keys()
        logging.info('Cities for {} '.format(name) + str(sorted(city_names)))

    def build_epoch(self, cut=False):
        """
        Perform Uniform Sampling per epoch to create a new list for training such that it
        uniformly samples all classes
        """
        if self.class_uniform_pct > 0:
            if cut:
                # after max_cu_epoch, we only fine images to fine tune
                self.imgs_uniform = uniform.build_epoch(self.imgs,
                                                        self.fine_centroids,
                                                        num_classes,
                                                        cfg.CLASS_UNIFORM_PCT)
            else:
                self.imgs_uniform = uniform.build_epoch(self.imgs + self.aug_imgs,
                                                        self.centroids,
                                                        num_classes,
                                                        cfg.CLASS_UNIFORM_PCT)
        else:
            self.imgs_uniform = self.imgs

    def __getitem__(self, index):
        elem = self.imgs_uniform[index]
        centroid = None
        if len(elem) == 4:
            img_path, mask_path, centroid, class_id = elem
        else:
            img_path, mask_path = elem
        img, mask = Image.open(img_path).convert('RGB'), Image.open(mask_path)
        img_name = os.path.splitext(os.path.basename(img_path))[0]

        mask = np.array(mask)
        mask_copy = mask.copy()
        for k, v in trainid_to_trainid.items():
            mask_copy[mask == k] = v
        mask = Image.fromarray(mask_copy.astype(np.uint8))

        # Image Transformations
        if self.extract_feature is not True:
            if self.joint_transform_list is not None:
                for idx, xform in enumerate(self.joint_transform_list):
                    if idx == 0 and centroid is not None:
                        # HACK
                        # We assume that the first transform is capable of taking
                        # in a centroid
                        img, mask = xform(img, mask, centroid)
                    else:
                        img, mask = xform(img, mask)

        # Debug
        if self.dump_images and centroid is not None:
            outdir = '../../dump_imgs_{}'.format(self.mode)
            os.makedirs(outdir, exist_ok=True)
            dump_img_name = trainid_to_name[class_id] + '_' + img_name
            out_img_fn = os.path.join(outdir, dump_img_name + '.png')
            out_msk_fn = os.path.join(outdir, dump_img_name + '_mask.png')
            mask_img = colorize_mask(np.array(mask))
            img.save(out_img_fn)
            mask_img.save(out_msk_fn)

        if self.transform is not None:
            img = self.transform(img)

        rgb_mean_std_gt = ([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
        img_gt = transforms.Normalize(*rgb_mean_std_gt)(img)

        rgb_mean_std = ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        if self.image_in:
            eps = 1e-5
            rgb_mean_std = ([torch.mean(img[0]), torch.mean(img[1]), torch.mean(img[2])],
                    [torch.std(img[0])+eps, torch.std(img[1])+eps, torch.std(img[2])+eps])
        img = transforms.Normalize(*rgb_mean_std)(img)

        if self.target_aux_transform is not None:
            mask_aux = self.target_aux_transform(mask)
        else:
            mask_aux = torch.tensor([0])
        if self.target_transform is not None:
            mask = self.target_transform(mask)

        return img, mask, img_name, mask_aux

    def __len__(self):
        return len(self.imgs_uniform)

class BDD100KDataSetAug(BaseDataset):

    def __init__(self, mode, maxSkip=0, joint_transform=None, sliding_crop=None,
                 transform=None, color_transform=None, geometric_transform=None, target_transform=None, target_aux_transform=None, dump_images=False,
                 cv_split=None, eval_mode=False,
                 eval_scales=None, eval_flip=False, image_in=False,
                 extract_feature=False):
        self.mode = mode
        self.maxSkip = maxSkip
        self.joint_transform = joint_transform
        self.sliding_crop = sliding_crop
        self.transform = transform
        self.color_transform = color_transform
        self.geometric_transform = geometric_transform
        self.target_transform = target_transform
        self.target_aux_transform = target_aux_transform
        self.dump_images = dump_images
        self.eval_mode = eval_mode
        self.eval_flip = eval_flip
        self.eval_scales = None
        self.image_in = image_in
        self.extract_feature = extract_feature


        if eval_scales != None:
            self.eval_scales = [float(scale) for scale in eval_scales.split(",")]

        if cv_split:
            self.cv_split = cv_split
            assert cv_split < cfg.DATASET.CV_SPLITS, \
                'expected cv_split {} to be < CV_SPLITS {}'.format(
                    cv_split, cfg.DATASET.CV_SPLITS)
        else:
            self.cv_split = 0
        self.imgs, _ = make_dataset(mode, self.maxSkip, cv_split=self.cv_split)
        if len(self.imgs) == 0:
            raise RuntimeError('Found 0 images, please check the data set')

        self.mean_std = ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])

    def _eval_get_item(self, img, mask, scales, flip_bool):
        return_imgs = []
        for flip in range(int(flip_bool) + 1):
            imgs = []
            if flip:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            for scale in scales:
                w, h = img.size
                target_w, target_h = int(w * scale), int(h * scale)
                resize_img = img.resize((target_w, target_h))
                tensor_img = transforms.ToTensor()(resize_img)
                final_tensor = transforms.Normalize(*self.mean_std)(tensor_img)
                imgs.append(final_tensor)
            return_imgs.append(imgs)
        return return_imgs, mask

    def __getitem__(self, index):

        img_path, mask_path = self.imgs[index]

        img, mask = Image.open(img_path).convert('RGB'), Image.open(mask_path)
        img_name = os.path.splitext(os.path.basename(img_path))[0]

        mask = np.array(mask)
        mask_copy = mask.copy()
        for k, v in trainid_to_trainid.items():
            mask_copy[mask == k] = v

        if self.eval_mode:
            return [transforms.ToTensor()(img)], self._eval_get_item(img, mask_copy,
                                                                     self.eval_scales,
                                                                     self.eval_flip), img_name

        mask = Image.fromarray(mask_copy.astype(np.uint8))

        if self.joint_transform is not None:
            img, mask = self.joint_transform(img, mask)

        if self.transform is not None:
            img_or = self.transform(img)

        if self.color_transform is not None:
            img_color = self.color_transform(img)

        if self.geometric_transform is not None:
            img_geometric = self.geometric_transform(img)

        rgb_mean_std_or = ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        rgb_mean_std_color = ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        rgb_mean_std_geometric = ([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        if self.image_in:
            eps = 1e-5
            rgb_mean_std_or = ([torch.mean(img_or[0]), torch.mean(img_or[1]), torch.mean(img_or[2])],
                    [torch.std(img_or[0])+eps, torch.std(img_or[1])+eps, torch.std(img_or[2])+eps])
            rgb_mean_std_color = ([torch.mean(img_color[0]), torch.mean(img_color[1]), torch.mean(img_color[2])],
                            [torch.std(img_color[0])+eps, torch.std(img_color[1])+eps, torch.std(img_color[2])+eps])
            rgb_mean_std_geometric = ([torch.mean(img_geometric[0]), torch.mean(img_geometric[1]), torch.mean(img_geometric[2])],
                            [torch.std(img_geometric[0])+eps, torch.std(img_geometric[1])+eps, torch.std(img_geometric[2])+eps])
        img_or = transforms.Normalize(*rgb_mean_std_or)(img_or)
        img_color = transforms.Normalize(*rgb_mean_std_color)(img_color)
        img_geometric = transforms.Normalize(*rgb_mean_std_geometric)(img_geometric)

        return img_or, img_color, img_geometric, img_name

    def __len__(self):
        return len(self.imgs)

if __name__ == "__main__":
	dataset = BDD100KDataSet('/data/BDD/', 'val', eval_mode=True)
	dataset[0]
	print(dataset[0])