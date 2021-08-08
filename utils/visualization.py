import matplotlib.pyplot as plt

def plot_all_sites (drone_image, crude, resized, filtered, site_no, cmap= 'Reds'):
    # Visualizing the development process of

    f, ax = plt.subplots(2, 2, sharey=False)
    ax[0,0].imshow(drone_image)
    ax[0,0].set_title('Drone RGB imagery')
    ax[0,0].set(xticks=[], yticks=[])

    sp1 = ax[0,1].imshow(crude, cmap=cmap)
    ax[0,1].set_title('Satellite Raw')
    ax[0,1].set(xticks=[], yticks=[])
    ax[0,1].set_label('AGB density (kg/px)')
    f.colorbar(sp1, ax=ax[0,1], shrink=0.9)

    sp2 = ax[1,0].imshow(resized, cmap=cmap)
    ax[1,0].set_title('Satellite Interpolated')
    ax[1,0].set(xticks=[], yticks=[])

    sp3 = ax[1,1].imshow(filtered, cmap=cmap)
    ax[1,1].set_title('Satellite Filtered')
    ax[1,1].set(xticks=[], yticks=[])
    ax[1,1].set_label('AGB density (kg/px)')
    f.colorbar(sp3, ax=ax[1,1], shrink=0.9)

    return


def compare_mean_AGB_density(field_data, site_no, map_crude, map_fitted, map_filtered):
    print('Mean AGB density:')

    field = field_data.loc[site_no, 'AGB density (tons/ha)']
    print('{}  : field data (ground truth)'.format(field.round(1)))

    crude = map_crude.mean()
    fitted = map_fitted.mean()
    filtered = map_filtered[map_filtered != 0].mean()

    print('{} : map_crude    : x{}  '.format(crude.round(1), (crude / field).round(1)))
    print('{} : map_fitted   : x{}  '.format(fitted.round(1), (fitted / field).round(1)))
    print('{} : map_filtered : x{}  '.format(filtered.round(1), (filtered / field).round(1)))
    print('The satellite-based map over/underestimates by a factor of {}'.format((filtered / field).round(1)))

    return


def AGB_density_analysis(results, field_data, site_no, map_filtered, map_name):
    field = field_data.loc[site_no, 'AGB density (tons/ha)']
    filtered = map_filtered[map_filtered != 0].mean()

    results = results.append({'site no': int(site_no),
                              'AGB density (field data)': field.round(0),
                              'AGB density (estimation from {})'.format(map_name): filtered.round(0),
                              'Factor for {}'.format(map_name): (filtered / field).round(1)
                              },
                             ignore_index=True)

    return results