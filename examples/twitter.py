import msteams as ms

# Twitter examlpe
card = ms.MessageCard(summary='Tweet Posted', title='Tweet Posted')
card.set_theme_color('0072C6')

section = ms.CardSection(text="A tweet with #MicrosoftTeams has been posted:")
section.add_fact("Posted By:", "Bill Gates")
section.add_fact("Posted at:", "2019-09-01")
section.add_fact("Tweet:", "#MicrosoftTeams is kind of neat.")

card.add_section(section)

action = ms.OpenUriAction(name='View All Tweets',
                          targets='https://twitter.com/search?q=%23MicrosoftTeams')
card.add_potential_action(action)

print(card.get_payload('json', indent=4))
