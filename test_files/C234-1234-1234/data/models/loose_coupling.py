from proxymod.model import Prox

def loose_coupling(config_1, config_2, config_3):
    """
    This function creates three instances of proxymod models. A configuration.ini
    file has been prepared for each.  This test utilizes the built in CSV files as
    data and transfers them to the next model in the configuration.
    """

    # instantiate first model
    model_1 = Prox(config=config_1,
                   model_name='loose_coupling_model_1',
                   start_yr=2010,
                   end_yr=2100,
                   step=5)
    # run model_1
    model_1.advance()

    # cleanup log objects
    model_1.close()

    # instantiate second model
    model_2 = Prox( config=config_2,
                    model_name='loose_coupling_model_2',
                    start_yr=2010,
                    end_yr=2100,
                    step=5,
                    in_one=model_1.out_file_1,
                    in_two=model_1.out_file_2)

    model_2.advance()
    model_2.close()

    # instantiate third model
    model_3 = Prox( config=config_3,
                    model_name='loose_coupling_model_3',
                    start_yr=2010,
                    end_yr=2100,
                    step=5,
                    in_one=model_2.out_file_1,
                    in_two=model_2.out_file_2)

    model_3.advance()
    model_3.close()
