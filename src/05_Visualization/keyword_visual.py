from pyvis.network import Network
import sys
import numpy as np
import webbrowser
import os
import random
from sklearn.manifold import MDS
from sklearn.preprocessing import MinMaxScaler
sys.path.append('./')
sys.path.append('./../')
sys.path.append('./../..')
if True:  # necesarry, so that auto-format does not move the import to top
    from src.utils.__RepoPath__ import repo_path
    from src.utils.logger import get_logger
    from news_page import News_Page
logger = get_logger('KEY_VIS')


def calculate_similarity_matrix(news_pages, eps=1):
    similarities = np.zeros((len(news_pages), len(news_pages)))
    for i in range(len(news_pages)):
        for j in range(i):
            similarities[i, j] = len(news_pages[i].common_keywords(
                news_pages[j])) + eps
            logger.debug(f'Dist between {i},{j} = {similarities[i,j]}')

    return similarities


def calculate_jacard_matrix(news_pages, eps=1):
    jaccard = np.zeros((len(news_pages), len(news_pages)))
    for i in range(len(news_pages)):
        for j in range(i):
            jaccard[i, j] = len(news_pages[i].common_keywords(
                news_pages[j]))/(len(news_pages[i].keywords | news_pages[j].keywords)+eps)
            logger.debug(f'Dist between {i},{j} = {jaccard[i,j]}')

    return jaccard


def calculate_colors(similarity_matrix):
    i_lower = np.tril_indices(similarity_matrix.shape[0], -1)
    similarity_matrix.T[i_lower] = similarity_matrix[i_lower]
    dissim = 1-similarity_matrix
    np.fill_diagonal(dissim, 0)
    embedding = MDS(n_components=3, dissimilarity='precomputed')
    scaler = MinMaxScaler()
    print(f'Dissimilarities:\n {dissim}')
    three_d = embedding.fit_transform(dissim)
    colors = (scaler.fit_transform(three_d)*255).astype(int)
    return colors


def create_graph(news_pages, num_keywords=6, color_keywords=False):
    jaccard = calculate_jacard_matrix(news_pages, eps=0)
    i_lower = np.tril_indices(jaccard.shape[0], -1)
    jaccard.T[i_lower] = jaccard[i_lower]
    np.fill_diagonal(jaccard, 1)
    colors = calculate_colors(jaccard)
    net = Network(height='100%', width='75%')
    net.inherit_edge_colors(True)
    net.barnes_hut()
    scan_images = os.listdir(os.path.join(repo_path, 'data', 'scan_examples'))
    scan_paths = ['file://' + os.path.join(
        repo_path, 'data', 'scan_examples', image) for image in scan_images]
    net.add_node('KEY', size=10*num_keywords, title='Flugblatt', label='Flugblatt', shape='image',
                 image='file:///Users/joel/Library/CloudStorage/OneDrive-Personal/_UNI/SS22/daVinci/data/example_flyer.jpg')
    for i, page in enumerate(news_pages):
        net.add_node(i, size=10*len(page.keywords),
                     title=page.name + '\n Keywords: \n' + '\n'.join(page.keywords), label=page.name.split('-')[-1], shape='image', image=random.choice(scan_paths), color=f'rgba{tuple(colors[i,:])+(0.7,)}')

    for i in range(len(news_pages)):
        for j in range(i):
            #similarity = similarities[i, j]
            # net.add_edge(i, j, weight=dist, value=dist,
            #              length=(100*np.max(similarities)/dist), physics=physics)
            common_words = news_pages[i].common_keywords(news_pages[j])
            similarity = len(common_words)
            jacc = jaccard[i, j]
            weight = jacc
            value = similarity
            length = int(100*(1-jacc)) + 1
            if similarity > 0:
                kwargs = dict(smooth=False,
                              title=',\n'.join(
                                  tuple(common_words)),
                              weight=weight,
                              value=value,
                              length=length
                              )

                if not color_keywords:
                    # Use default colors instead of inheritance
                    kwargs['color'] = '#83c5be'
                    kwargs['color.highlight'] = '#ffddd2'
                    kwargs['color.hover'] = 'red'
                net.add_edge(i, j,  **kwargs)

    for i, page in enumerate(news_pages):
        # Add in the end, so they are on top
        net.add_edge(i, 'KEY', weight=len(page.keywords), value=len(
            page.keywords), smooth=False, title=','.join(page.keywords))  # , color='#006d77')
    return net


def add_paper_to_net():
    pass


if __name__ == '__main__':
    import pickle
    import random
    with open('relations-cache.pkl', 'rb') as f:
        relations = pickle.load(f)
        logger.info(
            f'{relations} \n  ...loaded cached {len(relations)} relations:')
    random.seed(0)
    relations = random.sample(relations, 30)
    net = create_graph(relations, color_keywords=True)
    # print(net.generate_html())
    net.show(os.path.join(repo_path, 'key_vis.html'))
    webbrowser.open('file://' + os.path.join(repo_path,
                    'key_vis.html'), new=0, autoraise=True)
