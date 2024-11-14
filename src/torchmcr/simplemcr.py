from torchmcr.basemodel import MCR
import torch
import torch.nn as nn
import torch.nn.functional as F


class SimpleWeights(nn.Module):
    def __init__(self, M, K, preload_weights=None, modifier=nn.Softplus()):
        """
        Initialize the SimpleWeights object with optional preload and modifier.

        Parameters:
            M (int): Number of samples (rows).
            K (int): Number of components (columns).
            preload_weights (torch.Tensor, optional): Preloaded weight matrix, if provided.
            modifier (callable, optional): A function to modify the output, e.g., torch.nn.functional.softplus.
        """
        super(SimpleWeights, self).__init__()
        self.modifier = modifier
        # Initialize with preloaded weights or random values
        if preload_weights is not None:
            self.weight_matrix = nn.Parameter(preload_weights)
        else:
            self.weight_matrix = nn.Parameter(torch.rand(M, K))

    def forward(self):
        # Apply the modifier function if specified, else return the raw matrix
        if self.modifier:
            return self.modifier(self.weight_matrix)
        return self.weight_matrix


class SimpleSpectra(nn.Module):
    def __init__(self, K, N, preload_spectra=None, modifier=nn.Softplus()):
        """
        Initialize the SimpleSpectra object with optional preload and modifier.

        Parameters:
            K (int): Number of components (rows).
            N (int): Number of wavelengths (columns).
            preload_spectra (torch.Tensor, optional): Preloaded spectra matrix, if provided.
            modifier (callable, optional): A function to modify the output, e.g., torch.nn.functional.softplus.
        """
        super(SimpleSpectra, self).__init__()
        self.modifier = modifier
        # Initialize with preloaded spectra or random values
        if preload_spectra is not None:
            self.spectra_matrix = nn.Parameter(preload_spectra)
        else:
            self.spectra_matrix = nn.Parameter(torch.rand(K, N))

    def forward(self):
        # Apply the modifier function if specified, else return the raw matrix
        if self.modifier:
            return self.modifier(self.spectra_matrix)
        return self.spectra_matrix


class SimpleMCRModel(MCR):
    def __init__(
        self,
        M_samples,
        K_components,
        N_waves,
        preload_weights=None,
        preload_spectra=None,
        weights_modifier=None,
        spectra_modifier=None,
    ):
        """
        Initialize the SimpleMCRModel with optional preload and modifiers for weights and spectra.

        Parameters:
            M_samples (int): Number of samples (rows of weights matrix).
            K_components (int): Number of components (inner dimension).
            N_waves (int): Number of features (columns of spectra matrix).
            preload_weights (torch.Tensor, optional): Predefined weights matrix.
            preload_spectra (torch.Tensor, optional): Predefined spectra matrix.
            weights_modifier (callable, optional): Modifier function for weights.
            spectra_modifier (callable, optional): Modifier function for spectra.
        """
        weights = SimpleWeights(
            M_samples,
            K_components,
            preload_weights=preload_weights,
            modifier=weights_modifier,
        )
        spectra = SimpleSpectra(
            K_components,
            N_waves,
            preload_spectra=preload_spectra,
            modifier=spectra_modifier,
        )
        super(SimpleMCRModel, self).__init__(weights, spectra)
        # No additional initialization needed for SimpleMCRModel
        # All functionality is inherited from MCR base class
        pass
