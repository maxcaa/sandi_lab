import os
import shutil
import yaml
from deepof.data import Project  
import pandas as pd


def load_config():
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    return config


def create_project_folder(project_name):
    base_path = os.getcwd()  # or any specific path where you want to create project folders
    project_path = os.path.join(base_path, project_name)
    os.makedirs(project_path, exist_ok=True)
    
    video_path = os.path.join(project_path, 'videos')
    table_path = os.path.join(project_path, 'tables')
    os.makedirs(video_path, exist_ok=True)
    os.makedirs(table_path, exist_ok=True)

    # Create an initial config file
    config_data = {
        'video_path': video_path,
        'table_path': table_path,
        'project_path': project_path,
        'arena': 'polygonal-manual',
        'project_name': project_name,
        # 'exp_conditions': {
        #     'exp1': 'condition1',
        #     },
        'exclude_bodyparts': ['Tail_1', 'Tail_2', 'Tail_tip'],
        'bodypart_graph': 'deepof_14',
        'video_scale': 400,
        'preprocess_data': 'True'
    }
    config_path = os.path.join(project_path, 'config.yaml')
    with open(config_path, 'w') as file:
        yaml.dump(config_data, file)
    
    return project_path, config_path

def save_dataframes_to_excel(dataframes, file_path):
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        for sheet_name, df in dataframes.items():
            df.to_excel(writer, sheet_name=sheet_name)


def save_dataframes_to_pickle(dataframes, file_path):
    pd.to_pickle(dataframes, file_path)


def start_deepof(project_path):
    config_path = os.path.join(project_path, 'config.yaml')
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    
    # Extract necessary paths and settings from config
    project_path = config.get('project_path', '.')
    video_path = config['video_path']
    table_path = config['table_path']
    project_name = config['project_name']    
    exclude_bodyparts = config.get('exclude_bodyparts', [])
    bodypart_graph = config.get('bodypart_graph', 'deepof_14')
    arena = config.get('arena', 'polygonal-manual')
    video_scale = config['video_scale']
    exp_conditions = config.get('exp_conditions', {})
    preprocess_data = config.get('preprocess_data', True)
    
    if exp_conditions:
        print("Using provided experimental conditions:", exp_conditions)
        
        deepof_project = Project(
        project_path=project_path,
        video_path=video_path,
        table_path=table_path,
        project_name=project_name,
        exp_conditions=exp_conditions,
        exclude_bodyparts=exclude_bodyparts,
        bodypart_graph=bodypart_graph,
        arena=arena,
        video_scale=video_scale
    )
    else:
        print("No experimental conditions provided, proceeding without them.")
        deepof_project = Project(
        project_path=project_path,
        video_path=video_path,
        table_path=table_path,
        project_name=project_name,
        exclude_bodyparts=exclude_bodyparts,
        bodypart_graph=bodypart_graph,
        arena=arena,
        video_scale=video_scale
    )



    # Create the project
    deepof_project = deepof_project.create(verbose=True, force=False)

    # Run supervised annotation
    supervised = deepof_project.supervised_annotation()
    
    excel_path = os.path.join(project_path, 'supervised_data.xlsx')
    pickle_path = os.path.join(project_path, 'supervised_data.pkl')  
    save_dataframes_to_excel(supervised, excel_path)
    pd.to_pickle(supervised, pickle_path)
    if preprocess_data:
        filepath_freq = os.path.join(project_path, 'behavior_frequencies.xlsx')
        filepath_duration = os.path.join(project_path, 'behavior_durations.xlsx')
        preprocess_and_save(supervised, filepath_duration=filepath_duration, filepath_freq=filepath_freq)
    
    return supervised 


def load_project(folder_path):
    # Assuming this function sets the environment to work with a specific project
    print(f"Project loaded from {folder_path}")
    

    
    
####################################################################################################
# PREPROCESSING DATA

def reorganize_data(df):
    """Preprocess the speed data and structure event data."""
    mice_speed = pd.DataFrame(columns=['cage', 'Mouse', 'avg_speed', 'std_speed'])

    for key in df.keys():
        for mouse_id in ['individual1', 'individual2']:
            avg_speed = df[key][f'{mouse_id}_speed'].mean()
            std_speed = df[key][f'{mouse_id}_speed'].std()
            mice_speed = mice_speed.append({'cage': key, 'Mouse': mouse_id, 'avg_speed': avg_speed, 'std_speed': std_speed}, ignore_index=True)
            
    return mice_speed

def process_event_data(combined_data):
    event_freq_dict = {}
    row_events_dict = {}

    for key in combined_data.keys():
        time_standardisation = combined_data[key].shape[0] / 1500

        temp = combined_data[key]#.drop(columns=['individual1_speed', 'individual2_speed'])
        row_events = (pd.DataFrame(temp.sum(axis=0)).T) / time_standardisation
        row_events['cage'] = key
        event_switch = temp.diff(axis=0)
        event_freq = (pd.DataFrame(event_switch.applymap(lambda x: x if x > 0 else 0).sum()).T) / time_standardisation
        event_freq['cage'] = key

        row_events_dict[key] = row_events
        event_freq_dict[key] = event_freq

    row_events_df = pd.concat(row_events_dict, axis=0)
    event_freq_df = pd.concat(event_freq_dict, axis=0)

    return row_events_df, event_freq_df


def events_by_individual(supervised):
    '''
    Return object similar to TableDicts used in deepof: With multiindex to seperate the actions of individual 1 and 2 the actions that involve both individuals. 
    '''
    individual_1_interactions = ['individual1_individual2_nose2tail', 
                                 'individual1_individual2_nose2body', 
                                 'individual1_individual2_following']
    individual_1_solo = ['individual1_climbing', 'individual1_sniffing', 
                         'individual1_huddle', 'individual1_lookaround']

    individual_2_interactions = ['individual2_individual1_nose2tail', 
                                 'individual2_individual1_nose2body', 
                                 'individual2_individual1_following']
    individual_2_solo = ['individual2_climbing', 'individual2_sniffing',
                         'individual2_huddle', 'individual2_lookaround']

    mutual_actions = ['individual1_individual2_nose2nose', 'individual1_individual2_sidebyside', 
                      'individual1_individual2_sidereside']

    combined_data = {}

    for cage in supervised.keys():
        dat1_interactions = supervised[cage][individual_1_interactions].reindex(columns=individual_1_interactions)
        dat1_solo = supervised[cage][individual_1_solo].reindex(columns=individual_1_solo)
        dat1 = pd.concat([dat1_interactions, dat1_solo], keys=['interactions', 'solo'], axis=1)
        dat1.columns = dat1.columns.set_levels(
            ['nose2tail', 'nose2body', 'following', 'climbing', 'sniffing', 'huddle', 'lookaround'],
            level=1
            )

        dat2_interactions = supervised[cage][individual_2_interactions].reindex(columns=individual_2_interactions)
        dat2_solo = supervised[cage][individual_2_solo].reindex(columns=individual_2_solo)
        dat2 = pd.concat([dat2_interactions, dat2_solo], keys=['interactions', 'solo'], axis=1)
        dat2.columns = dat2.columns.set_levels(
            ['nose2tail', 'nose2body', 'following', 'climbing', 'sniffing', 'huddle', 'lookaround'],
            level=1
            )

        datMutual = supervised[cage][mutual_actions]
        datMutual.columns = pd.MultiIndex.from_product([['mutual'], datMutual.columns])

        combined_data[cage] = pd.concat([dat1, dat2, datMutual], keys=['individual1', 'individual2', 'mutual'], axis=1)

    return combined_data

def preprocess_and_save(supervised, filepath_freq='behavior_frequencies.xlsx', filepath_duration='behavior_durations.xlsx'):
    """Process and save data to Excel."""
    mice_speed = reorganize_data(supervised)
    preprocessed_data = events_by_individual(supervised)
    event_number, event_freq = process_event_data(preprocessed_data)
    
    # Combine and prepare final datasets for output
    for df_name, df in [('Frequency Data', event_freq), ('Duration Data', event_number)]:
        combined_df = pd.DataFrame()
        for mouse in ['individual1', 'individual2']:
            mouse_data = df[mouse].droplevel(0, axis=1)
            mouse_data['Mouse'] = mouse
            combined_df = pd.concat([combined_df, mouse_data], axis=0)
        combined_df = combined_df.reset_index(drop=True)
        combined_df = pd.concat([combined_df, mice_speed], axis=1).drop_duplicates().reset_index(drop=True)
        combined_df.to_excel(filepath_freq if df_name == 'Frequency Data' else filepath_duration, index=False)

    print("Data processed and saved to Excel.")


