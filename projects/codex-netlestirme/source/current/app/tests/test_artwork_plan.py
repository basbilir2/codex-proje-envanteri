import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from artwork_plan import instruction,validate,review_observation

class ArtworkPlanTests(unittest.TestCase):
    def observation(self):
        return dict(description='Two birds inside a geometric frame',composition='Birds overlap the center of the frame',intentional_texture='woodcut hatching',elements=[dict(kind='birds',appearance='two facing birds with solid wing fills',position='center',colors=['red','navy']),dict(kind='pattern',appearance='repeating triangles',position='border',colors=['cream'])],surface_effects=['fabric folds','cast shadow'],text=[],uncertainties=['exact cream ink shade'])
    def test_whole_design_without_any_text_is_supported(self):
        result=instruction(self.observation())
        for evidence in ['two facing birds','repeating triangles','red, navy','woodcut hatching','fabric folds','Birds overlap']:
            self.assertIn(evidence,result)
        self.assertNotIn('subtitle',result.lower())
        self.assertNotIn('lettering verbatim',result)
    def test_partial_lettering_does_not_become_a_guessed_word(self):
        o=self.observation();o['text']=[dict(visible_text='FIR',status='partial',position='upper left')]
        result=instruction(o)
        self.assertIn('do not invent a completion',result)
        self.assertNotIn('"FIRE"',result)
        self.assertNotIn('Keep the observed lettering verbatim',result)
    def test_unstructured_analysis_is_rejected(self):
        o=self.observation();o['elements']='just sharpen everything'
        with self.assertRaises(ValueError):validate(o)
    def test_missing_optional_text_position_preserves_supported_content(self):
        o=self.observation();o['text']=[dict(visible_text='BIRDS',status='clear')]
        result=instruction(o)
        self.assertIn('"BIRDS"',result)
        self.assertIn('its existing position in the reference',result)
    def test_uncertain_object_name_is_not_an_order_to_invent_that_object(self):
        o=self.observation();o['elements'][0].update(kind='bird',appearance='a narrow curved red form',visual_evidence='long pointed contour without a visible beak or feet',certainty='uncertain')
        text=instruction(o)
        self.assertNotIn('Preserve bird:',text)
        self.assertIn('pointed contour',text)
        self.assertIn('object identity uncertain',text)
    def test_review_requires_complete_observations_instead_of_only_approval(self):
        with self.assertRaises(ValueError):review_observation(dict(decision='supported',issues=[]))
    def test_rejected_review_is_preserved_as_rejected(self):
        result=review_observation(dict(decision='insufficient',issues=['The printed motif is too small'],observation=self.observation()))
        self.assertEqual(result['decision'],'insufficient')
    def test_artwork_box_cannot_escape_source_or_have_negative_extent(self):
        for box in ([0,0,1100,500],[700,0,200,500]):
            o=self.observation();o['artwork_box']=box
            with self.assertRaises(ValueError):validate(o)

if __name__=='__main__':unittest.main()
