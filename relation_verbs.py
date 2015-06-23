relDict = {
    "/r/RelatedTo": [
        ["evokes", "relates to", "echoes", "recalls", "educes", "elicits", "associates with"], 
        False],
    "/r/IsA": [
        ["is", "comprises", "constitutes", "encompasses", "amounts to"],
        True],
    "/r/PartOf": [
        ["appertains to", "is part of", "belongs to", "pertains to"],
        True],
    "/r/MemberOf": [
        ["appertains to", "is a member of", "belongs to", "pertains to", "is among"],
        True],
    "/r/HasA": [
        ["has", "enjoys", "holds", "includes", "owns", "retains"],
        True],
    "/r/UsedFor": [
        ["is for", "is used for", "is required for", "remains needed for", "is right for", "is requisite for"],
        False],
    "/r/CapableOf": [
        ["may", "is capable of", "might", "can"],
        False],
    #"/r/AtLocation": [False, False],
    "/r/Causes": [
        ["causes", "creates", "leads to", "brings about", "induces", "precipitates", "produces"],
        True],
    "/r/HasSubevent": [
        ["manifests", "precipitates", "results in", "leads to"],
        False],
    "/r/HasFirstSubevent": [
        ["begins with", "starts with", "results from"],
        True],
    "/r/HasLastSubevent": [
        ["ends with", "climaxes in", "finishes with"],
        True],
    "/r/HasPrerequisite": [
        ["requires", "demands", "expects", "involves"],
        True],
    "/r/HasProperty": [
        ["is", "has", "exhibits"],
        False],
    "/r/MotivatedByGoal": [
        ["dreams of", "craves", "longs for", "awaits", "lives for", "is motivated by"],
        False],
    "/r/ObstructedBy": [
        ["struggles with", "fights against", "confronts", "must overcome"],
        True],
    "/r/Desires": [
        ["yearns for", "desires", "wants", "longs for", "craves"],
        False],
    "/r/CreatedBy": [
        ["results from", "is created by", "comes from", "arises from"],
        True],
    "/r/Synonym": [
        ["is also known as", "could also be called"],
        True],
    "/r/Antonym": [
        ["is not", "is the opposite of", "is never"],
        True],
    "/r/DerivedFrom": [
        ["is made from", "derives from", "comes from", "results from", "arises from"],
        True],
    "/r/TranslationOf": [
        ["is known to some as", "translates to"],
        False],
    "/r/DefinedAs": [
        ["remains", "is defined as", "refers to", "is"],
        True]
}