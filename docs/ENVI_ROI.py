import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ee
def get_ENVI_ROIS(file,points_per_region=20):
    ### first scan the header to find out how many ROIs and what size they take in the file
    count = 0
    n_ROI_count = 0
    ROIS = {'ROI':[]}
    with open(file, 'rt') as f:
        for line in f:
            count+=1
            if 'Number of ROIs' in line:
                n_ROI = int(line[-2])
                ROIS['n_ROI'] = n_ROI
                ROI_split = [0]*n_ROI
            if 'ROI name' in line:
                ROIS['ROI'].append({'name':line.split('ROI name: ')[-1][:-1]})
            if 'ROI npts' in line:
                ROI_split[n_ROI_count] = int(line.split(' ')[-1][:-1])
                n_ROI_count+=1
            if n_ROI_count == n_ROI:
                print("Successfully loaded "+str(n_ROI)+" ROIs")
                break
    #### use pandas to read the rest of the data
    rois = pd.read_csv(file,header=None,skiprows=count+3)
    X_diff = np.diff(rois.values[:,0])
    Y_diff = np.diff(rois.values[:,1])
    #### find the 'chunks' within each ROI
    roi_change = np.logical_and(np.abs(X_diff)>2,np.abs(Y_diff)>2)
    roi_change_p = np.where(roi_change)
    n_ROI_sp = points_per_region
    ### use each ROI split to get each sub_ROI in each ROI
    ### extra variables for debugging
#     all_p = np.arange(rois.values.shape[0])
#     ROI_examples_lon = []
#     ROI_examples_lat = []
#     ROI_examples_p = []
    ### make a colour palette too for later
    Rcolors = ['#%02x%02x%02x' % tuple((int(c*254) for c in plt.cm.jet(n)[:-1])) 
           for n in range(0,255,int(255/n_ROI))]
    for nr in range(n_ROI):
        ROI_points = []
        ROI_i0 = int(np.sum(ROI_split[:nr]))
        ROI_i1 = np.sum(ROI_split[:nr+1])
        ROI_s = slice(ROI_i0,ROI_i1)
#         print(int(np.sum(ROI_split[:nr])),np.sum(ROI_split[:nr+1]))
        ROI_si = np.where(roi_change[ROI_s])
        if ROI_si[0].shape[0] == 0:
            ROI_si = (np.array([ROI_split[nr]]),)
        ROI_si0 = ROI_i0+2 ### start index (beginning), gets updated
        ROI_s_count = 0
        #### sub sample sub_ROI
        for ROI_sx in ROI_si[0]:
    #         print(ROI_i0,ROI_si0,ROI_si0+ROI_sx,ROI_i1)
#             print(ROI_si0,ROI_si0+ROI_sx,ROI_sx-ROI_si0+ROI_i0-2)
            k, m = divmod(ROI_sx-ROI_si0+ROI_i0-2, n_ROI_sp)
            for i in range(n_ROI_sp):
    #             lon_p = np.nanmean(rois.values[ROI_si0+i*k+min(i, m):
    #                                     ROI_si0+(i+1)*k+min(i+1, m),3]) 
    #             lat_p = np.nanmean(rois.values[ROI_si0+i*k+min(i, m):
    #                                     ROI_si0+(i+1)*k+min(i+1, m),2]) 
    #             p_p = np.nanmean(all_p[ROI_si0+i*k+min(i, m):
    #                                     ROI_si0+(i+1)*k+min(i+1, m)]) 
                lon_p = rois.values[ROI_si0+i*k+min(i, m),3]
                lat_p = rois.values[ROI_si0+i*k+min(i, m),2]
#                 p_p = all_p[ROI_si0+i*k+min(i, m)]
                if np.isfinite(lon_p):
                    #### generate a list of ee.Geometry.points
                    point = ee.Feature(ee.Geometry.Point(lon_p,lat_p) )
                    point = point.set('class',nr)
                    ROI_points.append(point)
#                     ROI_points.append(ee.Geometry.Point(lon_p,lat_p) )
#                     ROI_examples_lon.append(lon_p)
#                     ROI_examples_lat.append(lat_p)
#                     ROI_examples_p.append(p_p)
            ROI_si0 = ROI_i0+ ROI_sx+2
            ROI_s_count += 1
#         ROI_fcs.append(ee.FeatureCollection(ROI_points))
        print(ROIS['ROI'][nr]['name']+' total '+str(ROI_s_count)+' subregions')
        roiFC = ee.FeatureCollection(ROI_points)
        ROIS['ROI'][nr]['Points'] = roiFC# .set('class',nr)
        ROIS['ROI'][nr]['color'] = Rcolors[nr]
    return ROIS