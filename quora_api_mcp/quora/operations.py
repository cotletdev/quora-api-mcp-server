"""The persisted GraphQL operations the tools send: name to sha256, from Quora's Relay bundles (27.10.2026).

Only operations a tool uses are here, so `client.graphql` cannot send any other. A hash changes when Quora
rebuilds that query: the answer is then an error on a known operation, and the hash needs a new reading from
`window.ansFrontendRelayWebpackManifest`.
"""

from __future__ import annotations

READS = {
    "SearchResultsListQuery": "488f9d5679489416e25a114c378259beb70d3851857ababb387bd10f2a283e0c",
    "QuestionPageLoadablePreviewQuery": "14d65249d697d45a0c1771b651e3d70d236bca624dcd73770b4789e0bfc49069",
    "QuestionPagedListPaginationQuery": "4edd7d89166659f2cb492462a0c771d45f6585e249d8f0a090d9284790e84892",
    "UserProfileAnswersMostRecent_RecentAnswers_Query": (
        "0897a53b8eaef3e2d7d83ebc87f1527658bbcfc8c5c69655a77ceac2071993d6"
    ),
    "HighPriA2aRequestsListQuery": "7f09eb92513cfc898d70c6f4e024c569f6810d910b07e0392f3d7a0974d28aee",
    "LowPriA2aRequestsListQuery": "74fe50e542d9f4ae75baf432796273e80709a5eb5201bae60e15e6e0627bcaac",
    "YourSpacesSortedByRole_Paging_Query": "b6cd1c5ce2be4c887113586d92080be812491507d2fef842f90ef36ddc9e4f9e",
    "TribeStatsOverview_Query": "de28f0e0d19bbf7fd4bfa7eddde74a1707bd62fffb51785ca2ca44ff2a7e8434",
    "TribeStatsTopContentSectionQuery": "f210109267cbb1b0e52caaa4b536a209e653339012b971e6ac407b0aae49da30",
    "SubmissionsMultifeedQuery": "f3e7ad7331543b3ba0d7792faef03f12adda22f05b2aa1d175c7bc90d6531bb3",
    "TribeContentSourcesModalQuery": "e828f13623518ca97205d66236901b8ae3dbb6be4e2674addb3084d5a5abbb60",
    "UserProfilePageTabs_userQuery": "2afc50656e20c6137fafd96075f16bcc8418445777575658d71b82efd7bf4425",
    "UserProfileCredentialQuery": "08e7f8f718e855b2390f773746429266fbd051589a323252e9ebcb53ae3dcde4",
    "PostEditorHeaderQuery": "56cefbc7b467bba9f126826ebac1ff661f40970ee28a447224eb8dca2c24ce25",
    "NotifsPagedListWrapperQuery": "d2b25beaab6a358f94b1e9429b30a223cc7a6bb6ef4ce55f3a6df87074d0617e",
    "NotifsPagedList_LoadSentNotifCollection_Query": (
        "b4c58ccda93bf59e5b44186b8d556f8f319fb224240d3623d97c678dee56434e"
    ),
}

WRITES = {
    "AnswerEditorMutation_answerCreate_Mutation": "93127e7c752522a0114a1ada8438cbb85e3dc4b528efb58452df1745b7fd80a6",
    "askQuestionStepUtils_questionCreate_Mutation": "ed9852178c15f37737f64e27d136beb0152f97279e5707648a8a3556a6f7dece",
    "UniversalComposerModalWrapper_postAdd_Mutation": (
        "d9a78b89c8a0bba1a31de7f38176da640321ebec5914a185f2a9de57bb445459"
    ),
    "SubmissionAcceptButton_tribeSubmissionAccept_Mutation": (
        "d3ca9fa2ab1fff9e14699fb8c154d16160d1f1bc7f64200b3edb8c6146411ac0"
    ),
    "SubmissionRejectButton_tribeSubmissionReject_Mutation": (
        "4305616180e736b4aa0515ef4de1a9fcfff818dd721e05a4693f7273da0958ff"
    ),
    "SubmissionQueueButton_tribeSubmissionAddToContentQueue_Mutation": (
        "9276096b66231bad68db1b9a42189de57495dc3d9d3b50f87fcdbcd427830a53"
    ),
}
