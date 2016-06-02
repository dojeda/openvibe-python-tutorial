# openvibe-python-tutorial
OpenViBE Python scripting box examples

This tutorial should work with OpenViBE version 1.2.0. For a previous version, see note below.

## Notes for version <1.2.0

If you use the scenarios and Python code in this repository, you may
need to apply a small patch and recompile OpenViBE. More precisely,
during the parameter initialization of many OpenViBE processing boxes,
there is likely a call to `strtol` in order to convert from string to
long. The error handling code after this call forgets that the `errno`
variable must be set prior to calling `strtol`. The solution is
simple, set `errno=0` before calling `strtol`.

On version 1.2.0, this bug has been fixed.

This bug happens when some other code sets the `errno` prior to
OpenViBE's initialization. Which certainly happens in the code here
because `numpy.exp` underflows with some values (this is normal).

If you find that the scenario execution does not work, complaining
about an invalid parameter value, you may need to modify the code
before the `strtol` call. In my case, this happened in the temporal
filter box, so I had to do this modification:

```diff
--- a/contrib/plugins/processing/signal-processing/src/box-algorithms/ovpCTemporalFilterBoxAlgorithm.cpp
+++ b/contrib/plugins/processing/signal-processing/src/box-algorithms/ovpCTemporalFilterBoxAlgorithm.cpp
@@ -66,7 +66,7 @@ boolean CTemporalFilterBoxAlgorithm::initialize(void)
        TParameterHandler<uint64> ip_ui64KindFilter(m_pComputeTemporalFilterCoefficients->getInputParameter(OVP_Algorithm_ComputeTemporalFilterCoefficients_InputParameterId_FilterType));
        ip_ui64KindFilter=l_ui64UInteger64Parameter;
 
-
+       errno = 0;
        l_i64Integer64Parameter = strtol(l_oFilterOrder, &l_pEndPtr, 10);
        if(l_i64Integer64Parameter <= 0 || (errno !=0 && l_i64Integer64Parameter == 0) || *l_pEndPtr != '\0' || errno == ERANGE)
        {
```
