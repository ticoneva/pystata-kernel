import pandas as pd
import numpy as np
import pystata
import sfi

def better_pdataframe_from_data(var=None, obs=None, selectvar=None, valuelabel=False, missingval=np.NaN):
    pystata.config.check_initialized()

    return better_dataframe_from_stata(None, var, obs, selectvar, valuelabel, missingval)


def better_pdataframe_from_frame(stfr, var=None, obs=None, selectvar=None, valuelabel=False, missingval=np.NaN):
    pystata.config.check_initialized()

    return better_dataframe_from_stata(stfr, var, obs, selectvar, valuelabel, missingval)


def better_dataframe_from_stata(stfr, var, obs, selectvar, valuelabel, missingval):
    hdl = sfi.Data if stfr is None else sfi.Frame.connect(stfr)

    if hdl.getObsTotal() <= 0:
        return None

    pystata.stata.run("""tempvar indexvar
                         generate `indexvar' = _n""", quietly=True)
    idx_var = sfi.Macro.getLocal('indexvar')

    data = hdl.getAsDict(var, obs, selectvar, valuelabel, missingval)
    if idx_var in data:
        idx = data.pop(idx_var)
    else:
        idx = hdl.getAsDict(idx_var, obs, selectvar, valuelabel, missingval).pop(idx_var)

    idx = pd.array(idx, dtype='Int64')

    pystata.stata.run("drop `indexvar'")

    return pd.DataFrame(data=data, index=idx).convert_dtypes()
